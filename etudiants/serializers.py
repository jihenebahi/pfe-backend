# etudiants/serializers.py
from rest_framework import serializers
from .models import Etudiant, Document
from formation.models import Formation


class FormationMinSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Formation
        fields = ['id', 'intitule', 'duree', 'format', 'niveau']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Document
        fields = ['id', 'type_document', 'fichier', 'date_upload', 'commentaire']
        read_only_fields = ['date_upload']


class EtudiantSerializer(serializers.ModelSerializer):
    formations_noms           = serializers.CharField(read_only=True)
    nom_complet               = serializers.CharField(read_only=True)
    responsable_nom           = serializers.CharField(
        source='responsable.username', read_only=True, default=None)
    formations_suivies_detail = FormationMinSerializer(
        source='formations_suivies', many=True, read_only=True)
    documents                 = DocumentSerializer(many=True, read_only=True)

    class Meta:
        model  = Etudiant
        fields = [
            'id', 'nom', 'prenom', 'nom_complet', 'email', 'telephone',
            'ville', 'pays',
            'date_naissance', 'genre', 'niveau_etudes', 'diplome_obtenu',
            'formations_suivies', 'formations_suivies_detail', 'formations_noms',
            'date_inscription', 'statut', 'mode_paiement',
            'responsable', 'responsable_nom',
            'notes', 'documents',
            'date_creation', 'date_modification',
        ]
        read_only_fields = ['date_inscription', 'date_creation', 'date_modification']


# ── Serializer dédié à la création / mise à jour ──
class EtudiantCreateUpdateSerializer(serializers.ModelSerializer):
    formations_suivies = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Formation.objects.all(), required=False
    )

    class Meta:
        model  = Etudiant
        fields = '__all__'
        read_only_fields = ['date_inscription', 'date_creation', 'date_modification']
        extra_kwargs = {
            'responsable': {'required': False},
        }

    def create(self, validated_data):
        formations = validated_data.pop('formations_suivies', [])
        etudiant   = Etudiant.objects.create(**validated_data)
        etudiant.formations_suivies.set(formations)
        return etudiant

    def update(self, instance, validated_data):
        formations = validated_data.pop('formations_suivies', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if formations is not None:
            instance.formations_suivies.set(formations)
        return instance