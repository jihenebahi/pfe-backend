from rest_framework import serializers
from .models import Formation


class FormationSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)

    # Lecture : liste des formateurs avec id + nom complet
    formateurs_noms = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Formation
        fields = '__all__'

    def get_formateurs_noms(self, obj):
        return [
            {"id": f.id, "nom_complet": f"{f.prenom} {f.nom}"}
            for f in obj.formateurs.all()
        ]

    def create(self, validated_data):
        formateurs = validated_data.pop('formateurs', [])
        formation = Formation.objects.create(**validated_data)
        formation.formateurs.set(formateurs)
        return formation

    def update(self, instance, validated_data):
        formateurs = validated_data.pop('formateurs', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if formateurs is not None:
            instance.formateurs.set(formateurs)
        return instance