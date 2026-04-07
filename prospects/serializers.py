# prospects/serializers.py
from rest_framework import serializers
from .models import Prospect, HistoriqueEchange, Relance
from formation.models import Formation


class FormationMinSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Formation
        fields = ['id', 'intitule', 'duree', 'format', 'niveau']


class HistoriqueEchangeSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True)

    class Meta:
        model  = HistoriqueEchange
        fields = ['id', 'type_echange', 'date_echange',
                  'utilisateur', 'utilisateur_nom', 'contenu', 'notes']
        read_only_fields = ['date_echange']


class ProspectSerializer(serializers.ModelSerializer):
    historiques                  = HistoriqueEchangeSerializer(many=True, read_only=True)
    responsable_nom              = serializers.CharField(
        source='responsable.username', read_only=True, default=None)
    nom_complet                  = serializers.CharField(read_only=True)
    formations_souhaitees_detail = FormationMinSerializer(
        source='formations_souhaitees', many=True, read_only=True)
    formations_noms              = serializers.CharField(read_only=True)

    class Meta:
        model  = Prospect
        fields = [
            'id', 'nom', 'prenom', 'nom_complet', 'email', 'telephone',
            'ville', 'pays',
            'date_naissance', 'genre', 'niveau_etudes', 'diplome_obtenu',
            'source',
            'formations_souhaitees', 'formations_souhaitees_detail', 'formations_noms',
            'niveau_estime', 'mode_prefere',
            'canal_contact_prefere', 'commentaires',
            'statut', 'responsable', 'responsable_nom',
            'date_creation', 'date_modification',
            'ip_address', 'user_agent', 'historiques',
        ]
        read_only_fields = ['date_creation', 'date_modification', 'ip_address', 'user_agent']


class ProspectListSerializer(serializers.ModelSerializer):
    formations_noms = serializers.CharField(read_only=True)
    responsable_nom = serializers.CharField(
        source='responsable.username', read_only=True, default=None)

    class Meta:
        model  = Prospect
        fields = [
            'id', 'nom', 'prenom', 'email', 'telephone',
            'ville', 'pays',
            'date_naissance', 'genre', 'niveau_etudes', 'diplome_obtenu',
            'source',
            'formations_souhaitees', 'formations_noms',
            'niveau_estime', 'mode_prefere',
            'canal_contact_prefere', 'commentaires',
            'statut', 'responsable', 'responsable_nom', 'date_creation',
        ]


class ProspectCreateUpdateSerializer(serializers.ModelSerializer):
    formations_souhaitees = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Formation.objects.all(), required=False)

    email = serializers.EmailField(required=False, allow_blank=True, default='')

    class Meta:
        model  = Prospect
        fields = '__all__'
        read_only_fields = ['date_creation', 'date_modification']
        extra_kwargs = {
            'responsable': {'required': False},
        }

    def create(self, validated_data):
        formations = validated_data.pop('formations_souhaitees', [])
        prospect   = Prospect.objects.create(**validated_data)
        prospect.formations_souhaitees.set(formations)
        return prospect

    def update(self, instance, validated_data):
        formations = validated_data.pop('formations_souhaitees', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if formations is not None:
            instance.formations_souhaitees.set(formations)
        return instance


# ──────────────────────────────────────────────────────────────────────────────

class RelanceSerializer(serializers.ModelSerializer):
    """Serializer complet — utilisé pour le détail et la liste dashboard."""

    statut_calcule     = serializers.CharField(read_only=True)
    created_by_nom     = serializers.CharField(
        source='created_by.username', read_only=True, default=None
    )

    # Infos prospect dénormalisées
    prospect_nom       = serializers.CharField(source='prospect.nom',       read_only=True)
    prospect_prenom    = serializers.CharField(source='prospect.prenom',    read_only=True)
    prospect_telephone = serializers.CharField(source='prospect.telephone', read_only=True)

    # ✅ CORRECTION : formation_nom ajouté
    formation_nom      = serializers.CharField(
        source='formation.intitule', read_only=True, default=None
    )

    class Meta:
        model  = Relance
        fields = [
            'id',
            'prospect', 'prospect_nom', 'prospect_prenom', 'prospect_telephone',
            'formation', 'formation_nom',          # ✅ les deux champs ajoutés
            'date_relance', 'commentaire',
            'statut', 'statut_calcule',
            'date_action', 'created_by', 'created_by_nom',
            'date_creation',
        ]
        read_only_fields = ['date_action', 'date_creation', 'created_by']


class RelanceCreateSerializer(serializers.ModelSerializer):
    """Serializer allégé pour la création / mise à jour."""

    class Meta:
        model  = Relance
        fields = ['id', 'date_relance', 'commentaire', 'statut', 'formation']  # ✅ formation ajouté
        read_only_fields = []