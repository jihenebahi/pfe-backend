from rest_framework import serializers
from .models import Formation
from categories.serializers import CategorieSerializer

class FormationSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    
    class Meta:
        model = Formation
        fields = '__all__'
        extra_fields = ['categorie_nom']