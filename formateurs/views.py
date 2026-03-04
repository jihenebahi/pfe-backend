from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Formateur
from .serializers import FormateurSerializer


class FormateurListCreateView(APIView):
    """
    GET  /api/formateurs/       → Liste tous les formateurs
    POST /api/formateurs/       → Crée un nouveau formateur (avec fichiers PDF)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        formateurs = Formateur.objects.all().order_by('-date_creation')
        serializer = FormateurSerializer(formateurs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FormateurSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FormateurDetailView(APIView):
    """
    GET    /api/formateurs/<id>/   → Détail d'un formateur
    PUT    /api/formateurs/<id>/   → Modifier un formateur (avec fichiers PDF)
    DELETE /api/formateurs/<id>/   → Supprimer un formateur
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk):
        try:
            return Formateur.objects.get(pk=pk)
        except Formateur.DoesNotExist:
            return None

    def get(self, request, pk):
        formateur = self.get_object(pk)
        if not formateur:
            return Response({'error': 'Formateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = FormateurSerializer(formateur, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        formateur = self.get_object(pk)
        if not formateur:
            return Response({'error': 'Formateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = FormateurSerializer(
            formateur, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        formateur = self.get_object(pk)
        if not formateur:
            return Response({'error': 'Formateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        formateur.delete()
        return Response({'message': 'Formateur supprimé avec succès.'}, status=status.HTTP_204_NO_CONTENT)