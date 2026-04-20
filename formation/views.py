from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Formation
from .serializers import FormationSerializer
from categories.models import Categorie
from categories.serializers import CategorieSerializer
from formateurs.models import Formateur
from formateurs.serializers import FormateurSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_formations(request):
    """Retourne uniquement les formations ACTIVES (non archivées)"""
    formations = Formation.objects.filter(est_active=True).select_related('categorie').prefetch_related('formateurs').order_by('-date_creation')
    serializer = FormationSerializer(formations, many=True)
    return Response(serializer.data)


# ✅ NOUVEAU : Liste des formations archivées
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_formations_archivees(request):
    """Retourne uniquement les formations ARCHIVÉES (est_active=False)"""
    formations = Formation.objects.filter(est_active=False).select_related('categorie').prefetch_related('formateurs').order_by('-date_modification')
    serializer = FormationSerializer(formations, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ajouter_formation(request):
    serializer = FormationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detail_formation(request, pk):
    try:
        formation = Formation.objects.prefetch_related('formateurs').get(pk=pk)
    except Formation.DoesNotExist:
        return Response({'error': 'Formation non trouvée'}, status=status.HTTP_404_NOT_FOUND)

    serializer = FormationSerializer(formation)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def modifier_formation(request, pk):
    try:
        formation = Formation.objects.get(pk=pk)
    except Formation.DoesNotExist:
        return Response({'error': 'Formation non trouvée'}, status=status.HTTP_404_NOT_FOUND)

    serializer = FormationSerializer(formation, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def supprimer_formation(request, pk):
    try:
        formation = Formation.objects.get(pk=pk)
    except Formation.DoesNotExist:
        return Response({'error': 'Formation non trouvée'}, status=status.HTTP_404_NOT_FOUND)

    formation.delete()
    return Response({'message': 'Formation supprimée avec succès'}, status=status.HTTP_204_NO_CONTENT)


# ✅ NOUVEAU : Archiver une formation (est_active = False)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def archiver_formation(request, pk):
    try:
        formation = Formation.objects.get(pk=pk)
    except Formation.DoesNotExist:
        return Response({'error': 'Formation non trouvée'}, status=status.HTTP_404_NOT_FOUND)

    formation.est_active = False
    formation.save()
    serializer = FormationSerializer(formation)
    return Response(serializer.data)


# ✅ NOUVEAU : Réactiver une formation archivée (est_active = True)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def reactiver_formation(request, pk):
    try:
        formation = Formation.objects.get(pk=pk)
    except Formation.DoesNotExist:
        return Response({'error': 'Formation non trouvée'}, status=status.HTTP_404_NOT_FOUND)

    formation.est_active = True
    formation.save()
    serializer = FormationSerializer(formation)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_categories_pour_formations(request):
    categories = Categorie.objects.filter(actif=True).order_by('nom')
    serializer = CategorieSerializer(categories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_formateurs_pour_formations(request):
    formateurs = Formateur.objects.filter(est_actif=True).order_by('nom')
    serializer = FormateurSerializer(formateurs, many=True, context={'request': request})
    return Response(serializer.data)