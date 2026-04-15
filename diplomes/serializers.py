# diplomes/serializers.py
from rest_framework import serializers
from .models import Diplome, DiplomeRelance

class DiplomeRelanceSerializer(serializers.ModelSerializer):
    """Serializer complet pour les relances diplômés."""

    statut_calcule = serializers.CharField(read_only=True)
    created_by_nom = serializers.CharField(
        source='created_by.username', read_only=True, default=None
    )
    
    # NOUVEAU
    notes_action = serializers.CharField(read_only=True)

    # Infos diplômé dénormalisées
    diplome_nom = serializers.CharField(source='diplome.nom', read_only=True)
    diplome_prenom = serializers.CharField(source='diplome.prenom', read_only=True)
    diplome_telephone = serializers.CharField(source='diplome.telephone', read_only=True)
    diplome_email = serializers.CharField(source='diplome.email', read_only=True)
    diplome_formation = serializers.CharField(source='diplome.formation_intitule', read_only=True)

    formation_nom = serializers.CharField(
        source='formation.intitule', read_only=True, default=None
    )

    class Meta:
        model = DiplomeRelance
        fields = [
            'id',
            'diplome', 'diplome_nom', 'diplome_prenom',
            'diplome_telephone', 'diplome_email', 'diplome_formation',
            'formation', 'formation_nom',
            'date_relance', 'commentaire',
            'statut', 'statut_calcule',
            'date_action', 'notes_action',  # ← AJOUTÉ
            'created_by', 'created_by_nom',
            'date_creation',
        ]
        read_only_fields = ['date_action', 'date_creation', 'created_by', 'notes_action']


class DiplomeRelanceCreateSerializer(serializers.ModelSerializer):
    """Serializer allégé pour la création / mise à jour."""

    class Meta:
        model  = DiplomeRelance
        fields = ['id', 'date_relance', 'commentaire', 'statut', 'formation']
        read_only_fields = []


class DiplomeSerializer(serializers.ModelSerializer):
    nom_complet   = serializers.CharField(read_only=True)
    taux_presence = serializers.IntegerField(read_only=True)
    relances      = DiplomeRelanceSerializer(many=True, read_only=True)

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
            'relances',   # ← relances incluses dans le détail
        ]
        read_only_fields = ['date_creation', 'date_modification', 'nom_complet', 'taux_presence']