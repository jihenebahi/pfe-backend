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
    formations_noms              = serializers.CharField(read_only=True)
    nom_complet                  = serializers.CharField(read_only=True)
    responsable_nom              = serializers.CharField(
        source='responsable.username', read_only=True, default=None)
    formations_suivies_detail    = FormationMinSerializer(
        source='formations_suivies', many=True, read_only=True)
    documents                    = DocumentSerializer(many=True, read_only=True)

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