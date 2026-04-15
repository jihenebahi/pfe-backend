from django.contrib import admin
from .models import Diplome

@admin.register(Diplome)
class DiplomeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'prenom',
        'nom',
        'formation_intitule',
        'date_attestation',
        'taux_presence',
    ]
    
    list_filter = [
        'date_attestation',
        'date_creation',
        'formation',
    ]
    
    search_fields = [
        'nom',
        'prenom',
        'email',
        'formation_intitule',
    ]
    
    readonly_fields = [
        'date_creation',
        'date_modification',
        'nom_complet',
        'taux_presence',
    ]