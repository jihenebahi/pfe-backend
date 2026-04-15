# etudiants/serializers.py
from rest_framework import serializers
from .models import Etudiant, EtudiantFormation, Document, EtudiantRelance
from formation.models import Formation


class EtudiantFormationSerializer(serializers.ModelSerializer):
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


class DocumentSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_type_document_display', read_only=True
    )

    class Meta:
        model        = Document
        fields       = ['id', 'type_document', 'type_display',
                        'fichier', 'date_upload', 'commentaire']
        read_only_fields = ['date_upload']


# ──────────────────────────────────────────────────────────────────────────────
#  SERIALIZER POUR LES RELANCES ÉTUDIANTS
# ──────────────────────────────────────────────────────────────────────────────
# etudiants/serializers.py

class EtudiantRelanceSerializer(serializers.ModelSerializer):
    """Serializer complet pour les relances étudiants"""

    statut_calcule = serializers.CharField(read_only=True)
    created_by_nom = serializers.CharField(
        source='created_by.username', read_only=True, default=None
    )
    
    # NOUVEAU
    notes_action = serializers.CharField(read_only=True)

    # Infos étudiant dénormalisées
    etudiant_nom = serializers.CharField(source='etudiant.nom', read_only=True)
    etudiant_prenom = serializers.CharField(source='etudiant.prenom', read_only=True)
    etudiant_telephone = serializers.CharField(source='etudiant.telephone', read_only=True)
    etudiant_email = serializers.CharField(source='etudiant.email', read_only=True)

    formation_nom = serializers.CharField(
        source='formation.intitule', read_only=True, default=None
    )

    class Meta:
        model = EtudiantRelance
        fields = [
            'id',
            'etudiant', 'etudiant_nom', 'etudiant_prenom', 
            'etudiant_telephone', 'etudiant_email',
            'formation', 'formation_nom',
            'date_relance', 'commentaire',
            'statut', 'statut_calcule',
            'date_action', 'notes_action',  # ← AJOUTÉ notes_action
            'created_by', 'created_by_nom',
            'date_creation',
        ]
        read_only_fields = ['date_action', 'date_creation', 'created_by', 'notes_action']


class EtudiantRelanceCreateSerializer(serializers.ModelSerializer):
    """Serializer allégé pour la création / mise à jour"""

    class Meta:
        model  = EtudiantRelance
        fields = ['id', 'date_relance', 'commentaire', 'statut', 'formation']
        read_only_fields = []


# ──────────────────────────────────────────────────────────────────────────────
#  SERIALIZER PRINCIPAL ÉTUDIANT (sans prospect_id)
# ──────────────────────────────────────────────────────────────────────────────

class EtudiantSerializer(serializers.ModelSerializer):
    formations_noms     = serializers.CharField(read_only=True)
    nom_complet         = serializers.CharField(read_only=True)
    responsable_nom     = serializers.CharField(
        source='responsable.username', read_only=True, default=None
    )

    formations_suivies  = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True
    )

    formations_suivies_detail = EtudiantFormationSerializer(
        source='etudiant_formations', many=True, read_only=True
    )

    documents = DocumentSerializer(many=True, read_only=True)
    
    # Relances de l'étudiant
    relances = EtudiantRelanceSerializer(many=True, read_only=True)

    class Meta:
        model  = Etudiant
        fields = [
            'id', 'nom', 'prenom', 'nom_complet', 'email', 'telephone',
            'ville', 'pays',
            'date_naissance', 'genre', 'niveau_etudes', 'diplome_obtenu',
            'formations_suivies', 'formations_suivies_detail', 'formations_noms',
            'date_inscription', 'statut', 'mode_paiement',
            'responsable', 'responsable_nom',
            'notes', 'documents', 'relances',  # ← relances ajoutées
            'date_creation', 'date_modification',
        ]
        read_only_fields = ['date_inscription', 'date_creation', 'date_modification']


class EtudiantCreateUpdateSerializer(serializers.ModelSerializer):
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

            instance.etudiant_formations.filter(
                formation_id__in=current_ids - new_ids
            ).delete()

            for formation in formations:
                if formation.id not in current_ids:
                    EtudiantFormation.objects.create(
                        etudiant=instance, formation=formation
                    )

        return instance