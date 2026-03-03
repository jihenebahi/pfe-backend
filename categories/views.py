from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Categorie
from .serializers import CategorieSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_categories(request):
    categories = Categorie.objects.all().order_by('date_creation')
    
    # Ajouter le comptage des formations pour chaque catégorie
    data = []
    for categorie in categories:
        categorie_data = CategorieSerializer(categorie).data
        # Compter les formations liées
        categorie_data['formations_count'] = categorie.formations.count()
        data.append(categorie_data)
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ajouter_categorie(request):
    serializer = CategorieSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def modifier_categorie(request, pk):
    try:
        categorie = Categorie.objects.get(pk=pk)
    except Categorie.DoesNotExist:
        return Response({'detail': 'Catégorie introuvable.'}, status=status.HTTP_404_NOT_FOUND)

    # Vérifier si on essaie de désactiver une catégorie qui a des formations
    if request.data.get('actif') is False and categorie.formations.exists():
        return Response(
            {'detail': 'Impossible de désactiver : cette catégorie est liée à des formations.', 
             'code': 'has_formations'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = CategorieSerializer(categorie, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def supprimer_categorie(request, pk):
    try:
        categorie = Categorie.objects.get(pk=pk)
    except Categorie.DoesNotExist:
        return Response({'detail': 'Catégorie introuvable.'}, status=status.HTTP_404_NOT_FOUND)

    # Vérifier si la catégorie est liée à des formations
    if categorie.formations.exists():
        return Response(
            {'detail': 'Impossible de supprimer : cette catégorie est liée à des formations.', 
             'code': 'has_formations'},
            status=status.HTTP_400_BAD_REQUEST
        )

    categorie.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)