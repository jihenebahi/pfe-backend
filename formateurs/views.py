from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Formateur, ContratPDF, DiplomePDF
from .serializers import FormateurSerializer


class FormateurListCreateView(APIView):
    """
    GET  /api/formateurs/   → Liste tous les formateurs
    POST /api/formateurs/   → Crée un nouveau formateur (avec fichiers PDF multiples)
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        formateurs = (
            Formateur.objects
            .all()
            .prefetch_related('formations', 'contrats', 'diplomes')
            .order_by('-date_creation')
        )
        serializer = FormateurSerializer(formateurs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        errors = {}
        nom       = request.data.get('nom', '').strip()
        prenom    = request.data.get('prenom', '').strip()
        email     = request.data.get('email', '').strip()
        telephone = request.data.get('telephone', '').strip()

        # Doublon complet
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
            formateur = serializer.save(est_actif=True)  # ✅ toujours actif à la création

            # ✅ Enregistrer les contrats (multi-fichiers)
            for fichier in request.FILES.getlist('contrat_pdf'):
                ContratPDF.objects.create(formateur=formateur, fichier=fichier)

            # ✅ Enregistrer les diplômes (multi-fichiers)
            for fichier in request.FILES.getlist('diplomes_pdf'):
                DiplomePDF.objects.create(formateur=formateur, fichier=fichier)

            # Retourner le formateur avec toutes ses relations chargées
            formateur.refresh_from_db()
            out = FormateurSerializer(
                Formateur.objects.prefetch_related('formations', 'contrats', 'diplomes').get(pk=formateur.pk),
                context={'request': request}
            )
            return Response(out.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FormateurDetailView(APIView):
    """
    GET    /api/formateurs/<id>/   → Détail d'un formateur
    PUT    /api/formateurs/<id>/   → Modifier (fichiers PDF multiples)
    DELETE /api/formateurs/<id>/   → Supprimer
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk):
        try:
            return (
                Formateur.objects
                .prefetch_related('formations', 'contrats', 'diplomes')
                .get(pk=pk)
            )
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

            # ✅ Supprimer les contrats marqués pour suppression
            delete_contrats = request.data.getlist('delete_contrats')
            if delete_contrats:
                ContratPDF.objects.filter(
                    formateur=formateur,
                    id__in=[int(i) for i in delete_contrats if i.isdigit()]
                ).delete()

            # ✅ Supprimer les diplômes marqués pour suppression
            delete_diplomes = request.data.getlist('delete_diplomes')
            if delete_diplomes:
                DiplomePDF.objects.filter(
                    formateur=formateur,
                    id__in=[int(i) for i in delete_diplomes if i.isdigit()]
                ).delete()

            # ✅ Supprimer le CV si demandé
            if request.data.get('delete_cv') == 'true':
                if formateur.cv_pdf:
                    formateur.cv_pdf.delete(save=False)
                    formateur.cv_pdf = None
                    formateur.save(update_fields=['cv_pdf'])

            # ✅ Ajouter les nouveaux contrats
            for fichier in request.FILES.getlist('contrat_pdf'):
                ContratPDF.objects.create(formateur=formateur, fichier=fichier)

            # ✅ Ajouter les nouveaux diplômes
            for fichier in request.FILES.getlist('diplomes_pdf'):
                DiplomePDF.objects.create(formateur=formateur, fichier=fichier)

            # Retourner les données fraîches
            out = FormateurSerializer(
                Formateur.objects.prefetch_related('formations', 'contrats', 'diplomes').get(pk=pk),
                context={'request': request}
            )
            return Response(out.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        formateur = self.get_object(pk)
        if not formateur:
            return Response({'error': 'Formateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        # Bloquer la suppression si formations associées
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