# diplomes/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.utils import timezone
from datetime import date

from .models import Diplome, DiplomeRelance
from .serializers import DiplomeSerializer, DiplomeRelanceSerializer, DiplomeRelanceCreateSerializer


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

    search    = request.query_params.get('search')
    formation = request.query_params.get('formation')

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
    GET    /api/diplomes/<pk>/
    DELETE /api/diplomes/<pk>/
    """
    diplome = get_object_or_404(
        Diplome.objects.prefetch_related('relances__formation', 'relances__created_by'),
        pk=pk
    )

    if request.method == 'GET':
        return Response(DiplomeSerializer(diplome).data)

    elif request.method == 'DELETE':
        diplome.delete()
        return Response(
            {'message': 'Diplômé supprimé avec succès.'},
            status=status.HTTP_204_NO_CONTENT,
        )


# ──────────────────────────────────────────────────────────────────────
#  ENVOYER ATTESTATION PAR EMAIL
# ──────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def envoyer_attestation(request, pk):
    """POST /api/diplomes/<pk>/envoyer-attestation/"""
    diplome = get_object_or_404(Diplome, pk=pk)

    if not diplome.email:
        return Response(
            {'error': 'Aucun email disponible pour ce diplômé.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        taux = 0
        presences = 0
        if diplome.seances_total > 0:
            presences = diplome.seances_total - diplome.absences
            taux = round((presences / diplome.seances_total) * 100)

        sujet = f"Attestation de Réussite — {diplome.formation_intitule}"

        formation_duree_html = (
            f'<div style="font-size: 13px; color: #666; margin-top: 5px;">Durée : {diplome.formation_duree}</div>'
            if diplome.formation_duree else ''
        )

        presences_html = (
            f'''<div class="info-block">
                <div class="info-label">Taux de présence</div>
                <div class="info-value">{taux}%</div>
                <div style="font-size: 13px; color: #666; margin-top: 5px;">({presences} séances sur {diplome.seances_total})</div>
            </div>'''
            if diplome.seances_total > 0 else ''
        )

        message_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; color: #333; }}
    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
    .header {{ background: linear-gradient(135deg,#1A6B4A,#0F4B35); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
    .content {{ background: #f8f9fa; border: 1px solid #e9ecef; border-top: none; padding: 30px; border-radius: 0 0 8px 8px; }}
    .info-block {{ background: white; border-left: 4px solid #1A6B4A; padding: 15px; margin: 20px 0; border-radius: 4px; }}
    .info-label {{ color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
    .info-value {{ color: #1A6B4A; font-weight: 600; font-size: 16px; }}
    .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #999; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1>🎓 Attestation de Réussite</h1></div>
    <div class="content">
      <p>Chère <strong>{diplome.prenom} {diplome.nom}</strong>,</p>
      <p>Votre attestation de réussite est disponible.</p>
      <div class="info-block">
        <div class="info-label">Formation</div>
        <div class="info-value">{diplome.formation_intitule or '—'}</div>
        {formation_duree_html}
      </div>
      <div class="info-block">
        <div class="info-label">Date de l'attestation</div>
        <div class="info-value">{diplome.date_attestation}</div>
      </div>
      {presences_html}
      <p><strong>Félicitations ! 🎉</strong></p>
      <div class="footer">© Centre de Formation Professionnelle — {diplome.date_attestation.year}</div>
    </div>
  </div>
</body>
</html>"""

        send_mail(
            subject=sujet,
            message=f"Attestation de réussite pour {diplome.formation_intitule}",
            from_email=None,
            recipient_list=[diplome.email],
            html_message=message_html,
            fail_silently=False,
        )

        return Response(
            {'message': f'Attestation envoyée avec succès à {diplome.email}'},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {'error': f"Erreur lors de l'envoi de l'email : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ──────────────────────────────────────────────────────────────────────
#  CERTIFICATION
# ──────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def certifier_etudiant(request):
    """POST /api/diplomes/certifier/"""
    from etudiants.models import Etudiant

    etudiant_id      = request.data.get('etudiant_id')
    formation_id     = request.data.get('formation_id')
    date_attestation = request.data.get('date_attestation')

    if not all([etudiant_id, formation_id, date_attestation]):
        return Response(
            {'error': 'Les champs etudiant_id, formation_id et date_attestation sont obligatoires.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    etudiant = get_object_or_404(Etudiant, pk=etudiant_id)

    if not etudiant.formations_suivies.filter(pk=formation_id).exists():
        return Response(
            {'error': "Cette formation ne fait pas partie des formations suivies par l'étudiant."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if Diplome.objects.filter(etudiant_id_origine=etudiant_id, formation_id=formation_id).exists():
        return Response(
            {'error': 'Une attestation existe déjà pour cette formation et cet étudiant.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    formation = etudiant.formations_suivies.get(pk=formation_id)

    diplome = Diplome.objects.create(
        nom       = etudiant.nom,
        prenom    = etudiant.prenom,
        email     = etudiant.email     or '',
        telephone = etudiant.telephone or '',
        ville     = getattr(etudiant, 'ville', '') or '',
        pays      = getattr(etudiant, 'pays',  '') or '',
        notes     = etudiant.notes     or '',
        formation          = formation,
        formation_intitule = formation.intitule,
        formation_duree    = f"{formation.duree}h" if formation.duree else '',
        date_attestation    = date_attestation,
        etudiant_id_origine = etudiant.id,
    )

    total_formations = etudiant.formations_suivies.count()
    certifiees_count = Diplome.objects.filter(etudiant_id_origine=etudiant.id).count()

    etudiant_supprime = False
    if certifiees_count >= total_formations:
        etudiant.delete()
        etudiant_supprime = True

    return Response(
        {
            'diplome':           DiplomeSerializer(diplome).data,
            'etudiant_supprime': etudiant_supprime,
            'certifiees':        certifiees_count,
            'total':             total_formations,
        },
        status=status.HTTP_201_CREATED,
    )


# ══════════════════════════════════════════════════════════════════════
#  RELANCES D'UN DIPLÔMÉ
# ══════════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def diplome_relance_list_create(request, diplome_pk):
    """
    GET  /api/diplomes/<pk>/relances/  → liste des relances d'un diplômé
    POST /api/diplomes/<pk>/relances/  → créer une relance
    """
    diplome = get_object_or_404(Diplome, pk=diplome_pk)

    if request.method == 'GET':
        relances = diplome.relances.select_related('formation', 'created_by').all()
        return Response(DiplomeRelanceSerializer(relances, many=True).data)

    elif request.method == 'POST':
        serializer = DiplomeRelanceCreateSerializer(data=request.data)
        if serializer.is_valid():
            formation = serializer.validated_data.get('formation')
            # Si pas de formation fournie, utiliser celle du diplôme
            if not formation and diplome.formation:
                formation = diplome.formation

            relance = serializer.save(
                diplome=diplome,
                created_by=request.user,
                formation=formation,
            )
            return Response(
                DiplomeRelanceSerializer(relance).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def diplome_relance_detail(request, pk):
    """
    GET    /api/diplomes/relances/<pk>/
    PATCH  /api/diplomes/relances/<pk>/
    DELETE /api/diplomes/relances/<pk>/
    """
    relance = get_object_or_404(DiplomeRelance, pk=pk)

    if request.method == 'GET':
        return Response(DiplomeRelanceSerializer(relance).data)

    elif request.method == 'PATCH':
        serializer = DiplomeRelanceCreateSerializer(relance, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(DiplomeRelanceSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        relance.delete()
        return Response({'message': 'Relance supprimée.'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def diplome_relance_action_ok(request, pk):
    """
    POST /api/diplomes/relances/<pk>/ok/
    Marque la relance comme effectuée.
    """
    relance = get_object_or_404(DiplomeRelance, pk=pk)
    relance.statut = 'fait'
    relance.date_action = timezone.now()
    relance.notes_action = request.data.get('notes', '')  # ← NOUVEAU
    relance.save()

    return Response(
        {
            'message': 'Relance marquée comme effectuée.',
            'relance': DiplomeRelanceSerializer(relance).data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_diplome_relances(request):
    """
    GET /api/diplomes/relances/all/
    Toutes les relances diplômés — pour le dashboard Home.
    """
    relances = DiplomeRelance.objects.select_related(
        'diplome', 'created_by', 'formation'
    ).all()
    return Response(DiplomeRelanceSerializer(relances, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def diplome_relances_count_today(request):
    """Compteur des relances diplômé du jour (badge navbar)."""
    today = date.today()
    count = DiplomeRelance.objects.filter(
        date_relance__lte=today
    ).exclude(statut='fait').count()
    return Response({'count': count})