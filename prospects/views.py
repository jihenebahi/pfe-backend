# prospects/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Prospect, HistoriqueEchange
from .serializers import (
    ProspectSerializer,
    ProspectListSerializer,
    ProspectCreateUpdateSerializer,
    HistoriqueEchangeSerializer,
)


# ──────────────────────────────────────────────
#  LISTE + CRÉATION
# ──────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def prospect_list_create(request):
    """
    GET  /api/prospects/        → liste paginée avec filtres
    POST /api/prospects/        → créer un nouveau prospect
    """
    if request.method == 'GET':
        queryset = Prospect.objects.select_related('responsable') \
                                   .prefetch_related('formations_souhaitees').all()

        # ── Filtres optionnels ──
        statut  = request.query_params.get('statut')
        source  = request.query_params.get('source')
        search  = request.query_params.get('search')

        if statut:
            queryset = queryset.filter(statut=statut)
        if source:
            queryset = queryset.filter(source=source)
        if search:
            queryset = queryset.filter(
                nom__icontains=search
            ) | queryset.filter(
                prenom__icontains=search
            ) | queryset.filter(
                email__icontains=search
            ) | queryset.filter(
                telephone__icontains=search
            )

        serializer = ProspectListSerializer(queryset, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ProspectCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            # Capture l'IP du client
            x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
                  # ✅ MODIFICATION: Ajouter automatiquement l'utilisateur connecté comme responsable
            prospect = serializer.save(
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                responsable=request.user  # ← Ajout automatique du responsable
            )
            return Response(
                ProspectSerializer(prospect).data,
                status=status.HTTP_201_CREATED
            )      

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
#  DÉTAIL + MODIFICATION + SUPPRESSION
# ──────────────────────────────────────────────
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def prospect_detail(request, pk):
    """
    GET    /api/prospects/<pk>/  → détail complet avec historiques
    PUT    /api/prospects/<pk>/  → modification complète
    PATCH  /api/prospects/<pk>/  → modification partielle
    DELETE /api/prospects/<pk>/  → suppression
    """
    prospect = get_object_or_404(Prospect, pk=pk)

    if request.method == 'GET':
        serializer = ProspectSerializer(prospect)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ProspectCreateUpdateSerializer(
            prospect, data=request.data, partial=partial
        )
        if serializer.is_valid():
            updated = serializer.save()
            return Response(ProspectSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        prospect.delete()
        return Response(
            {'message': 'Prospect supprimé avec succès.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ──────────────────────────────────────────────
#  HISTORIQUE DES ÉCHANGES
# ──────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def historique_list_create(request, prospect_pk):
    """
    GET  /api/prospects/<pk>/historiques/   → liste des échanges
    POST /api/prospects/<pk>/historiques/   → ajouter un échange
    """
    prospect = get_object_or_404(Prospect, pk=prospect_pk)

    if request.method == 'GET':
        historiques = prospect.historiques.all()
        serializer = HistoriqueEchangeSerializer(historiques, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = HistoriqueEchangeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(prospect=prospect, utilisateur=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
#  STATISTIQUES RAPIDES (dashboard)
# ──────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prospect_stats(request):
    """
    GET /api/prospects/stats/  → compteurs par statut
    """
    from django.db.models import Count
    stats = Prospect.objects.values('statut').annotate(count=Count('id'))
    result = {item['statut']: item['count'] for item in stats}
    result['total'] = Prospect.objects.count()
    return Response(result)



# ──────────────────────────────────────────────
#  CONVERSION PROSPECT → ÉTUDIANT
# ──────────────────────────────────────────────
# prospects/views.py - modifier la fonction convert_to_etudiant

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def convert_to_etudiant(request, pk):
    """
    POST /api/prospects/<pk>/convert/
    Crée un Etudiant à partir du prospect, puis supprime le prospect.
    Body attendu :
      {
        "formations_ids":   [1, 2],
        "statut_etudiant":  "Actif",
        "notes":            "...",
        "documents_fournis": ["CIN", "CV", "Contrat", ...]  # ← AJOUT
      }
    """
    from etudiants.models import Etudiant, Document  # ← IMPORT Document
    from formation.models import Formation

    prospect = get_object_or_404(Prospect, pk=pk)

    # ── Mappings FR → slug Django ──
    STATUT_MAP = {
        'Actif':     'actif',
        'Abandonné': 'abandonne',
        'Certifié':  'certifie',
    }
    
    # ── Mapping pour les types de documents ──
    DOCUMENT_TYPE_MAP = {
        'CIN':      'cin',
        'CV':       'cv',
        'Contrat':  'contrat',
        'Reçu':     'recu',
        'RNE':      'rne',
        'Autres':   'autre',
    }

    statut          = STATUT_MAP.get(request.data.get('statut_etudiant', 'Actif'), 'actif')
    mode_paiement   = 'espece'
    formations_ids  = request.data.get('formations_ids', [])
    notes           = request.data.get('notes', '')
    documents_fournis = request.data.get('documents_fournis', [])  # ← RÉCUPÉRATION

    # ── Création de l'étudiant ──
    etudiant = Etudiant(
        nom           = prospect.nom,
        prenom        = prospect.prenom,
        email         = prospect.email,
        telephone     = prospect.telephone,
        ville         = prospect.ville,
        pays          = prospect.pays,
        date_naissance= prospect.date_naissance,
        genre         = prospect.genre,
        niveau_etudes = prospect.niveau_etudes,
        diplome_obtenu= prospect.diplome_obtenu,
        statut        = statut,
        mode_paiement = mode_paiement,
        responsable   = request.user,
        notes         = notes,
    )
    etudiant.save()

    # ── Création des documents (sans fichier, juste pour tracer la présence) ──
    for doc in documents_fournis:
        doc_type = DOCUMENT_TYPE_MAP.get(doc, 'autre')
        Document.objects.create(
            etudiant=etudiant,
            type_document=doc_type,
            fichier=None,  # Pas de fichier uploadé, juste un enregistrement
            commentaire=f"Document fourni en version physique : {doc}"
        )

    # ── Formations ──
    if formations_ids:
        formations = Formation.objects.filter(id__in=formations_ids)
        etudiant.formations_suivies.set(formations)
    else:
        etudiant.formations_suivies.set(prospect.formations_souhaitees.all())

    # ── Suppression du prospect ──
    prospect.delete()

    return Response(
        {'message': 'Prospect converti en étudiant avec succès.', 'etudiant_id': etudiant.id},
        status=status.HTTP_201_CREATED
    )