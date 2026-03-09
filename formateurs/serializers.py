from rest_framework import serializers
from .models import Formateur


# ✅ Serializer léger pour afficher les formations liées avec id + intitule
class FormationCourteSerializer(serializers.Serializer):
    id       = serializers.IntegerField()
    intitule = serializers.CharField()


class FormateurSerializer(serializers.ModelSerializer):

    # Retourne l'URL complète pour chaque fichier PDF (ex: http://localhost:8000/media/...)
    contrat_pdf  = serializers.FileField(required=False, allow_null=True)
    cv_pdf       = serializers.FileField(required=False, allow_null=True)
    diplomes_pdf = serializers.FileField(required=False, allow_null=True)

    # ✅ AJOUT : retourne les formations avec {id, intitule} au lieu de simples IDs
    formations = FormationCourteSerializer(many=True, read_only=True)

    class Meta:
        model  = Formateur
        fields = '__all__'
        read_only_fields = ['date_creation', 'date_modification']

    def to_representation(self, instance):
        """Retourne les URLs absolues pour les fichiers PDF."""
        ret = super().to_representation(instance)
        request = self.context.get('request')

        for field in ['contrat_pdf', 'cv_pdf', 'diplomes_pdf']:
            file_obj = getattr(instance, field)
            if file_obj and hasattr(file_obj, 'url'):
                ret[field] = request.build_absolute_uri(file_obj.url) if request else file_obj.url
            else:
                ret[field] = None

        return ret