from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Formation
from .serializers import FormationSerializer
from categories.models import Categorie
from categories.serializers import CategorieSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_formations(request):
    formations = Formation.objects.all().select_related('categorie').order_by('-date_creation')
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
        formation = Formation.objects.get(pk=pk)
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_categories_pour_formations(request):
    categories = Categorie.objects.filter(actif=True).order_by('nom')
    serializer = CategorieSerializer(categories, many=True)
    return Response(serializer.data)