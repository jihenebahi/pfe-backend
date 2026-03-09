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
        formateurs = Formateur.objects.all().prefetch_related('formations').order_by('-date_creation')
        serializer = FormateurSerializer(formateurs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        errors = {}
        nom       = request.data.get('nom', '').strip()
        prenom    = request.data.get('prenom', '').strip()
        email     = request.data.get('email', '').strip()
        telephone = request.data.get('telephone', '').strip()

        # Doublon complet : même nom + prénom + email + téléphone
        if nom and prenom and email and Formateur.objects.filter(
            nom__iexact=nom,
            prenom__iexact=prenom,
            email__iexact=email,
            telephone=telephone
        ).exists():
            errors['non_field_errors'] = (
                "Un formateur avec le même nom, prénom, email et téléphone existe déjà."
            )

        # Unicité email
        if email and Formateur.objects.filter(email__iexact=email).exists():
            errors['email'] = "Cette adresse email est déjà utilisée par un autre formateur."

        # Unicité téléphone
        if telephone and Formateur.objects.filter(telephone=telephone).exists():
            errors['telephone'] = "Ce numéro de téléphone est déjà utilisé par un autre formateur."

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

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
            return Formateur.objects.prefetch_related('formations').get(pk=pk)
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

        errors = {}
        email     = request.data.get('email', '').strip()
        telephone = request.data.get('telephone', '').strip()

        # Unicité email (exclure le formateur lui-même)
        if email and Formateur.objects.filter(email__iexact=email).exclude(pk=pk).exists():
            errors['email'] = "Cette adresse email est déjà utilisée par un autre formateur."

        # Unicité téléphone (exclure le formateur lui-même)
        if telephone and Formateur.objects.filter(telephone=telephone).exclude(pk=pk).exists():
            errors['telephone'] = "Ce numéro de téléphone est déjà utilisé par un autre formateur."

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

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

        # ── Bloquer la suppression si formations associées ────────────────────
        nb_formations = formateur.formations.count()
        if nb_formations > 0:
            noms = list(formateur.formations.values_list('intitule', flat=True))
            return Response(
                {
                    'error': 'suppression_bloquee',
                    'message': (
                        f"Impossible de supprimer ce formateur : il est associé à "
                        f"{nb_formations} formation(s)."
                    ),
                    'formations': noms,
                },
                status=status.HTTP_409_CONFLICT
            )

        formateur.delete()
        return Response(
            {'message': 'Formateur supprimé avec succès.'},
            status=status.HTTP_204_NO_CONTENT
        )