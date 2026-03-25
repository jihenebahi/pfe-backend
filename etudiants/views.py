# etudiants/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Etudiant
from .serializers import EtudiantSerializer, EtudiantCreateUpdateSerializer


# ──────────────────────────────────────────────
#  LISTE + CRÉATION
# ──────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def etudiant_list_create(request):
    """
    GET  /api/etudiants/   → liste avec filtres optionnels
    POST /api/etudiants/   → créer un nouvel étudiant
    """
    if request.method == 'GET':
        queryset = (
            Etudiant.objects
            .select_related('responsable')
            .prefetch_related('formations_suivies', 'documents')
            .all()
        )

        # ── Filtres optionnels ──
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
    etudiant = get_object_or_404(Etudiant, pk=pk)

    if request.method == 'GET':
        serializer = EtudiantSerializer(etudiant)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial    = request.method == 'PATCH'
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