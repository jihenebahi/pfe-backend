# diplomes/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Diplome
from .serializers import DiplomeSerializer


# ──────────────────────────────────────────────────────────────────────
#  LISTE
# ──────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def diplome_list(request):
    """
    GET /api/diplomes/
    Filtres optionnels : ?search=  ?formation=<id>
    """
    qs = Diplome.objects.select_related('formation').all()

    search     = request.query_params.get('search')
    formation  = request.query_params.get('formation')

    if search:
        qs = (
            qs.filter(nom__icontains=search)
            | qs.filter(prenom__icontains=search)
            | qs.filter(email__icontains=search)
        )
    if formation:
        qs = qs.filter(formation_id=formation)

    serializer = DiplomeSerializer(qs, many=True)
    return Response(serializer.data)


# ──────────────────────────────────────────────────────────────────────
#  DÉTAIL + SUPPRESSION
# ──────────────────────────────────────────────────────────────────────
@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def diplome_detail(request, pk):
    """
    GET    /api/diplomes/<pk>/  → détail
    DELETE /api/diplomes/<pk>/  → suppression
    """
    diplome = get_object_or_404(Diplome, pk=pk)

    if request.method == 'GET':
        return Response(DiplomeSerializer(diplome).data)

    elif request.method == 'DELETE':
        diplome.delete()
        return Response(
            {'message': 'Diplômé supprimé avec succès.'},
            status=status.HTTP_204_NO_CONTENT,
        )


# ──────────────────────────────────────────────────────────────────────
#  CERTIFICATION  ← endpoint principal de conversion
# ──────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def certifier_etudiant(request):
    """
    POST /api/diplomes/certifier/

    Body JSON :
    {
        "etudiant_id"      : <int>,
        "formation_id"     : <int>,
        "date_attestation" : "YYYY-MM-DD"
    }

    Logique métier :
    ─────────────────────────────────────────────────────
    1. Valide que l'étudiant existe et que la formation
       fait bien partie de ses formations_suivies.
    2. Vérifie qu'aucune attestation n'existe déjà
       pour cette paire (étudiant, formation).
    3. Crée un enregistrement Diplome en copiant
       les informations de l'étudiant (snapshot).
    4. Compare le nombre de formations totales de
       l'étudiant avec le nombre de Diplomes créés
       pour lui.
       • Si toutes les formations sont certifiées
         → supprime définitivement l'étudiant.
       • Sinon → l'étudiant reste dans la table.
    5. Retourne { diplome, etudiant_supprime: bool }.
    """
    from etudiants.models import Etudiant  # import local pour éviter les imports circulaires

    # ── 1. Validation des paramètres ────────────────────────────────
    etudiant_id      = request.data.get('etudiant_id')
    formation_id     = request.data.get('formation_id')
    date_attestation = request.data.get('date_attestation')

    if not all([etudiant_id, formation_id, date_attestation]):
        return Response(
            {'error': 'Les champs etudiant_id, formation_id et date_attestation sont obligatoires.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── 2. Récupérer l'étudiant ──────────────────────────────────────
    etudiant = get_object_or_404(Etudiant, pk=etudiant_id)

    # ── 3. Vérifier que la formation est suivie par l'étudiant ───────
    if not etudiant.formations_suivies.filter(pk=formation_id).exists():
        return Response(
            {'error': "Cette formation ne fait pas partie des formations suivies par l'étudiant."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── 4. Vérifier l'unicité (pas de double attestation) ───────────
    if Diplome.objects.filter(
        etudiant_id_origine=etudiant_id,
        formation_id=formation_id,
    ).exists():
        return Response(
            {'error': 'Une attestation existe déjà pour cette formation et cet étudiant.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── 5. Créer le diplôme (snapshot) ──────────────────────────────
    formation = etudiant.formations_suivies.get(pk=formation_id)

    diplome = Diplome.objects.create(
        # Snapshot identité
        nom       = etudiant.nom,
        prenom    = etudiant.prenom,
        email     = etudiant.email     or '',
        telephone = etudiant.telephone or '',
        ville     = getattr(etudiant, 'ville', '') or '',
        pays      = getattr(etudiant, 'pays',  '') or '',
        notes     = etudiant.notes     or '',
        # Formation
        formation          = formation,
        formation_intitule = formation.intitule,
        formation_duree    = f"{formation.duree}h" if formation.duree else '',
        # Attestation
        date_attestation    = date_attestation,
        # Référence historique
        etudiant_id_origine = etudiant.id,
    )

    # ── 6. Logique de suppression ────────────────────────────────────
    total_formations  = etudiant.formations_suivies.count()
    certifiees_count  = Diplome.objects.filter(etudiant_id_origine=etudiant.id).count()

    etudiant_supprime = False
    if certifiees_count >= total_formations:
        etudiant.delete()
        etudiant_supprime = True

    # ── 7. Réponse ───────────────────────────────────────────────────
    return Response(
        {
            'diplome':           DiplomeSerializer(diplome).data,
            'etudiant_supprime': etudiant_supprime,
            'certifiees':        certifiees_count,
            'total':             total_formations,
        },
        status=status.HTTP_201_CREATED,
    )