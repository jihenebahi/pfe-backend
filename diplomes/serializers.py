# diplomes/serializers.py
from rest_framework import serializers
from .models import Diplome


class DiplomeSerializer(serializers.ModelSerializer):
    nom_complet    = serializers.CharField(read_only=True)
    taux_presence  = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Diplome
        fields = [
            'id',
            'nom', 'prenom', 'nom_complet',
            'email', 'telephone', 'ville', 'pays', 'notes',
            'formation', 'formation_intitule', 'formation_duree',
            'date_attestation',
            'seances_total', 'absences', 'taux_presence',
            'etudiant_id_origine',
            'date_creation', 'date_modification',
        ]
        read_only_fields = ['date_creation', 'date_modification', 'nom_complet', 'taux_presence']