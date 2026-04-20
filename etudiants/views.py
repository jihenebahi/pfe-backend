# etudiants/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import date

from .models import Etudiant, EtudiantFormation, EtudiantRelance
from .serializers import (
    EtudiantSerializer, 
    EtudiantCreateUpdateSerializer,
    EtudiantRelanceSerializer,
    EtudiantRelanceCreateSerializer
)


# ──────────────────────────────────────────────
#  LISTE + CRÉATION
# ──────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def etudiant_list_create(request):
    """
    GET  /api/etudiants/  → liste avec filtres optionnels (statut, search)
    POST /api/etudiants/  → créer un nouvel étudiant
    """
    if request.method == 'GET':
        queryset = (
            Etudiant.objects
            .select_related('responsable')
            .prefetch_related(
                'etudiant_formations__formation',
                'documents',
            )
            .all()
        )

        statut = request.query_params.get('statut')
        search = request.query_params.get('search')

        if statut:
            queryset = queryset.filter(statut=statut)
        if search:
            queryset = (
                queryset.filter(nom__icontains=search)
                | queryset.filter(prenom__icontains=search)
                | queryset.filter(email__icontains=search)
                | queryset.filter(telephone__icontains=search)
            )

        serializer = EtudiantSerializer(queryset, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = EtudiantCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            etudiant = serializer.save(responsable=request.user)
            return Response(
                EtudiantSerializer(etudiant).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
#  DÉTAIL + MODIFICATION + SUPPRESSION
# ──────────────────────────────────────────────

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def etudiant_detail(request, pk):
    """
    GET    /api/etudiants/<pk>/  → détail complet
    PUT    /api/etudiants/<pk>/  → modification complète
    PATCH  /api/etudiants/<pk>/  → modification partielle
    DELETE /api/etudiants/<pk>/  → suppression
    """
    etudiant = get_object_or_404(
        Etudiant.objects
        .select_related('responsable')
        .prefetch_related('etudiant_formations__formation', 'documents'),
        pk=pk,
    )

    if request.method == 'GET':
        return Response(EtudiantSerializer(etudiant).data)

    elif request.method in ['PUT', 'PATCH']:
        partial    = (request.method == 'PATCH')
        serializer = EtudiantCreateUpdateSerializer(
            etudiant, data=request.data, partial=partial
        )
        if serializer.is_valid():
            updated = serializer.save()
            return Response(EtudiantSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        etudiant.delete()
        return Response(
            {'message': 'Étudiant supprimé avec succès.'},
            status=status.HTTP_204_NO_CONTENT,
        )


# ──────────────────────────────────────────────
#  ATTESTER UNE FORMATION
# ──────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def attester_formation(request, pk, formation_pk):
    """
    POST /api/etudiants/<pk>/formations/<formation_pk>/attester/

    Marque la formation comme attestée pour cet étudiant.
    Body (optionnel) : { "date_attestation": "YYYY-MM-DD" }
    """
    etudiant = get_object_or_404(Etudiant, pk=pk)

    try:
        ef = EtudiantFormation.objects.get(
            etudiant=etudiant, formation_id=formation_pk
        )
    except EtudiantFormation.DoesNotExist:
        return Response(
            {'error': "Cette formation n'est pas associée à cet étudiant."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if ef.attestation:
        return Response(
            {'error': "Cette formation a déjà été attestée."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    date_attestation = request.data.get('date_attestation')
    ef.attestation = True
    if date_attestation:
        ef.date_attestation = date_attestation
    ef.save()

    # Recharger avec les relations pour le serializer
    etudiant.refresh_from_db()
    etudiant_fresh = (
        Etudiant.objects
        .select_related('responsable')
        .prefetch_related('etudiant_formations__formation', 'documents')
        .get(pk=pk)
    )
    return Response(EtudiantSerializer(etudiant_fresh).data)



# ──────────────────────────────────────────────────────────────────────────────
#  RELANCES D'UN ÉTUDIANT (NOUVEAU - INDÉPENDANT)
# ──────────────────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def etudiant_relance_list_create(request, etudiant_pk):
    """
    GET  /api/etudiants/<pk>/relances/  → Liste des relances d'un étudiant
    POST /api/etudiants/<pk>/relances/  → Créer une relance pour un étudiant
    """
    etudiant = get_object_or_404(Etudiant, pk=etudiant_pk)

    if request.method == 'GET':
        relances = etudiant.relances.select_related('formation', 'created_by').all()
        serializer = EtudiantRelanceSerializer(relances, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = EtudiantRelanceCreateSerializer(data=request.data)
        if serializer.is_valid():
            formation = serializer.validated_data.get('formation')
            if not formation:
                formation = etudiant.formations_suivies.first()
                
            relance = serializer.save(
                etudiant=etudiant,
                created_by=request.user,
                formation=formation,
            )
            return Response(
                EtudiantRelanceSerializer(relance).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def etudiant_relance_detail(request, pk):
    """
    GET    /api/etudiants/relances/<pk>/  → Détail d'une relance
    PATCH  /api/etudiants/relances/<pk>/  → Modifier une relance
    DELETE /api/etudiants/relances/<pk>/  → Supprimer une relance
    """
    relance = get_object_or_404(EtudiantRelance, pk=pk)

    if request.method == 'GET':
        return Response(EtudiantRelanceSerializer(relance).data)

    elif request.method == 'PATCH':
        serializer = EtudiantRelanceCreateSerializer(relance, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(EtudiantRelanceSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        relance.delete()
        return Response(
            {'message': 'Relance supprimée.'},
            status=status.HTTP_204_NO_CONTENT
        )


# etudiants/views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def etudiant_relance_action_ok(request, pk):
    """
    POST /api/etudiants/relances/<pk>/ok/
    
    Marque la relance comme effectuée.
    """
    relance = get_object_or_404(EtudiantRelance, pk=pk)

    relance.statut = 'fait'
    relance.date_action = timezone.now()
    relance.notes_action = request.data.get('notes', '')  # ← NOUVEAU
    relance.save()

    return Response(
        {
            'message': 'Relance marquée comme effectuée.',
            'relance': EtudiantRelanceSerializer(relance).data,
        },
        status=status.HTTP_200_OK
    )



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def etudiant_relances_count_today(request):
    """Compteur des relances étudiant du jour"""
    today = date.today()
    count = EtudiantRelance.objects.filter(
        date_relance__lte=today
    ).exclude(statut='fait').count()
    return Response({'count': count})



# etudiants/views.py
# Ajoutez cette fonction après les autres fonctions de relance

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_etudiant_relances(request):
    """
    GET /api/etudiants/relances/all/
    Retourne toutes les relances étudiants (pour le dashboard)
    """
    relances = EtudiantRelance.objects.select_related('etudiant', 'created_by', 'formation').all()
    serializer = EtudiantRelanceSerializer(relances, many=True)
    return Response(serializer.data)




# etudiants/views.py
# Ajoutez cette fonction après les autres fonctions de relance

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_etudiant_relances(request):
    """
    GET /api/etudiants/relances/all/
    Retourne toutes les relances étudiants (pour le dashboard)
    """
    relances = EtudiantRelance.objects.select_related('etudiant', 'created_by', 'formation').all()
    serializer = EtudiantRelanceSerializer(relances, many=True)
    return Response(serializer.data)


