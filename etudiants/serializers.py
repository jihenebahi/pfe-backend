# etudiants/serializers.py
from rest_framework import serializers
from .models import Etudiant, EtudiantFormation, Document
from formation.models import Formation


# ──────────────────────────────────────────────────────────────────
#  Formation légère (pour le champ formations_suivies_detail)
# ──────────────────────────────────────────────────────────────────

class EtudiantFormationSerializer(serializers.ModelSerializer):
    """
    Expose les données du through model EtudiantFormation :
    - champs de la formation (id, intitule, duree, format, niveau)
    - champs propres à l'inscription (date, attestation, date_attestation)
    """
    id       = serializers.IntegerField(source='formation.id',       read_only=True)
    intitule = serializers.CharField(source='formation.intitule',    read_only=True)
    duree    = serializers.SerializerMethodField()
    format   = serializers.CharField(source='formation.format',      read_only=True)
    niveau   = serializers.CharField(source='formation.niveau',      read_only=True)

    def get_duree(self, obj):
        return obj.formation.duree

    class Meta:
        model  = EtudiantFormation
        fields = [
            'id', 'intitule', 'duree', 'format', 'niveau',
            'date_inscription_formation',
            'attestation', 'date_attestation',
        ]


# ──────────────────────────────────────────────────────────────────
#  Document
# ──────────────────────────────────────────────────────────────────

class DocumentSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_document_display', read_only=True
    )

    class Meta:
        model        = Document
        fields       = ['id', 'type_document', 'type_display',
                        'fichier', 'date_upload', 'commentaire']
        read_only_fields = ['date_upload']


# ──────────────────────────────────────────────────────────────────
#  Lecture complète d'un étudiant
# ──────────────────────────────────────────────────────────────────

class EtudiantSerializer(serializers.ModelSerializer):
    formations_noms     = serializers.CharField(read_only=True)
    nom_complet         = serializers.CharField(read_only=True)
    responsable_nom     = serializers.CharField(
        source='responsable.username', read_only=True, default=None
    )

    # IDs bruts (pour les filtres / formulaire React)
    formations_suivies  = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True
    )

    # Données enrichies par formation (via through model)
    formations_suivies_detail = EtudiantFormationSerializer(
        source='etudiant_formations', many=True, read_only=True
    )

    documents = DocumentSerializer(many=True, read_only=True)

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


# ──────────────────────────────────────────────────────────────────
#  Création / mise à jour
# ──────────────────────────────────────────────────────────────────

class EtudiantCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Désérialise les IDs de formations, puis gère manuellement
    la table de liaison EtudiantFormation (through model).
    """
    formations_suivies = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Formation.objects.all(),
        required=False,
    )

    class Meta:
        model  = Etudiant
        fields = [
            'id', 'nom', 'prenom', 'email', 'telephone', 'ville', 'pays',
            'date_naissance', 'genre', 'niveau_etudes', 'diplome_obtenu',
            'formations_suivies', 'statut', 'mode_paiement',
            'responsable', 'notes',
            'date_inscription', 'date_creation', 'date_modification',
        ]
        read_only_fields = ['date_inscription', 'date_creation', 'date_modification']
        extra_kwargs = {
            # ── CORRECTION : tous les champs optionnels marqués required=False ──
            # Cela évite les erreurs 400 lors d'un PATCH partiel
            'responsable':    {'required': False},
            'statut':         {'required': False},
            'mode_paiement':  {'required': False},
            'ville':          {'required': False},
            'telephone':      {'required': False},
            'pays':           {'required': False},
            'date_naissance': {'required': False},
            'genre':          {'required': False},
            'niveau_etudes':  {'required': False},
            'diplome_obtenu': {'required': False},
            'notes':          {'required': False},
        }

    def create(self, validated_data):
        formations = validated_data.pop('formations_suivies', [])
        etudiant   = Etudiant.objects.create(**validated_data)
        for formation in formations:
            EtudiantFormation.objects.create(
                etudiant=etudiant, formation=formation
            )
        return etudiant

    def update(self, instance, validated_data):
        formations = validated_data.pop('formations_suivies', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if formations is not None:
            current_ids = set(
                instance.etudiant_formations.values_list('formation_id', flat=True)
            )
            new_ids = set(f.id for f in formations)

            # Supprimer les formations retirées
            instance.etudiant_formations.filter(
                formation_id__in=current_ids - new_ids
            ).delete()

            # Ajouter les nouvelles formations
            for formation in formations:
                if formation.id not in current_ids:
                    EtudiantFormation.objects.create(
                        etudiant=instance, formation=formation
                    )

        return instance