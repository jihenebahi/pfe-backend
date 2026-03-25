from rest_framework import serializers
from .models import Formateur, ContratPDF, DiplomePDF


# ✅ Serializer formations (lecture seule — pour afficher les formations liées)
class FormationCourteSerializer(serializers.Serializer):
    id       = serializers.IntegerField()
    intitule = serializers.CharField()


# ✅ Serializers pour les fichiers multiples
class ContratPDFSerializer(serializers.ModelSerializer):
    fichier_url = serializers.SerializerMethodField()

    class Meta:
        model  = ContratPDF
        fields = ['id', 'fichier', 'fichier_url', 'date_ajout']
        read_only_fields = ['date_ajout']

    def get_fichier_url(self, obj):
        request = self.context.get('request')
        if obj.fichier and hasattr(obj.fichier, 'url'):
            return request.build_absolute_uri(obj.fichier.url) if request else obj.fichier.url
        return None


class DiplomePDFSerializer(serializers.ModelSerializer):
    fichier_url = serializers.SerializerMethodField()

    class Meta:
        model  = DiplomePDF
        fields = ['id', 'fichier', 'fichier_url', 'date_ajout']
        read_only_fields = ['date_ajout']

    def get_fichier_url(self, obj):
        request = self.context.get('request')
        if obj.fichier and hasattr(obj.fichier, 'url'):
            return request.build_absolute_uri(obj.fichier.url) if request else obj.fichier.url
        return None


# ✅ Serializer principal Formateur
class FormateurSerializer(serializers.ModelSerializer):

    # CV — URL absolue
    cv_pdf = serializers.FileField(required=False, allow_null=True)

    # Formations liées (lecture seule)
    formations = FormationCourteSerializer(many=True, read_only=True)

    # Contrats et diplômes en lecture (liste d'objets)
    contrats  = ContratPDFSerializer(many=True, read_only=True)
    diplomes  = DiplomePDFSerializer(many=True, read_only=True)

    class Meta:
        model  = Formateur
        fields = [
            'id', 'nom', 'prenom', 'email', 'telephone', 'adresse',
            'specialites', 'niveau_intervention', 'type_contrat',
            'cv_pdf',
            'contrats', 'diplomes',   # ✅ listes multi-fichiers
            'formations',
            'est_actif', 'date_creation', 'date_modification',
        ]
        read_only_fields = ['date_creation', 'date_modification']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        # URL absolue pour le CV
        if instance.cv_pdf and hasattr(instance.cv_pdf, 'url'):
            ret['cv_pdf'] = request.build_absolute_uri(instance.cv_pdf.url) if request else instance.cv_pdf.url
        else:
            ret['cv_pdf'] = None
        return ret