# prospects/serializers.py
from rest_framework import serializers
from .models import Prospect, HistoriqueEchange
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
            # ← champs hérités de PersonneBase
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

    class Meta:
        model  = Prospect
        fields = '__all__'
        read_only_fields = ['date_creation', 'date_modification']

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