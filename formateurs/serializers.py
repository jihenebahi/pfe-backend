from rest_framework import serializers
from .models import Formateur


class FormateurSerializer(serializers.ModelSerializer):

    class Meta:
        model = Formateur
        fields = '__all__'