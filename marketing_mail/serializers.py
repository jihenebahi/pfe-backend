# marketing_mail/serializers.py

from rest_framework import serializers
from .models import MarketingEmail, DestinatairEmail
from formation.models import Formation


class DestinatairEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinatairEmail
        fields = (
            'id', 'email_adresse', 'type_destinataire',
            'prospect', 'etudiant', 'diplome', 'date_envoi'
        )
        read_only_fields = fields


class MarketingEmailListSerializer(serializers.ModelSerializer):
    envoye_par_email = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = MarketingEmail
        fields = (
            'id', 'objet', 'envoye_par_email', 'groupe',
            'groupe_display', 'nombre_destinataires',
            'est_archive', 'send_mode', 'date'
        )

    def get_envoye_par_email(self, obj):
        if obj.envoye_par:
            return obj.envoye_par.email or obj.envoye_par.username
        return "—"

    def get_date(self, obj):
        return obj.date_envoi.strftime('%d/%m/%Y')


class MarketingEmailSerializer(serializers.ModelSerializer):
    envoye_par_nom = serializers.SerializerMethodField(read_only=True)
    envoye_par_email = serializers.SerializerMethodField(read_only=True)
    destinataires = DestinatairEmailSerializer(many=True, read_only=True)
    
    # Utiliser PrimaryKeyRelatedField pour les formations
    formations_cibles = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Formation.objects.all(),
        required=False
    )

    class Meta:
        model = MarketingEmail
        fields = (
            'id',
            'envoye_par', 'envoye_par_nom', 'envoye_par_email',
            'objet', 'apercu', 'message', 'fichier',
            'send_mode', 'email_direct',
            'groupe', 'groupe_display',
            'formations_cibles', 'statuts_prospects', 'sources_prospects',
            'nombre_destinataires', 'est_archive',
            'date_envoi', 'date_modification',
            'destinataires',
        )
        read_only_fields = (
            'envoye_par', 'envoye_par_nom', 'envoye_par_email',
            'groupe_display', 'nombre_destinataires',
            'date_envoi', 'date_modification', 'destinataires'
        )

    def get_envoye_par_nom(self, obj):
        if obj.envoye_par:
            return obj.envoye_par.get_full_name() or obj.envoye_par.username
        return "—"

    def get_envoye_par_email(self, obj):
        if obj.envoye_par:
            return obj.envoye_par.email or obj.envoye_par.username
        return "—"

    def validate(self, data):
        send_mode = data.get('send_mode', 'segment')

        if send_mode == 'direct':
            if not data.get('email_direct'):
                raise serializers.ValidationError(
                    {"email_direct": "L'adresse e-mail est obligatoire en mode envoi direct."}
                )
        else:
            if not data.get('groupe'):
                raise serializers.ValidationError(
                    {"groupe": "Le groupe cible est obligatoire en mode segment."}
                )

        if not data.get('objet'):
            raise serializers.ValidationError({"objet": "La ligne d'objet est obligatoire."})

        if not data.get('message'):
            raise serializers.ValidationError({"message": "Le corps du message est obligatoire."})

        return data

    def create(self, validated_data):
        formations = validated_data.pop('formations_cibles', [])
        instance = super().create(validated_data)
        if formations:
            instance.formations_cibles.set(formations)
        return instance


class ArchiveEmailSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )


class EstimationDestinatairesSerializer(serializers.Serializer):
    groupe = serializers.ChoiceField(choices=MarketingEmail.GROUPE_CHOICES)
    formations_cibles = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    statuts_prospects = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    sources_prospects = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )