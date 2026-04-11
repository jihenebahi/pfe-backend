# diplomes/admin.py

from django.contrib import admin
from .models import Diplome

@admin.register(Diplome)
class DiplomeAdmin(admin.ModelAdmin):
    list_display = [
        'numero_diplome', 'nom_complet', 'formation', 
        'type_document', 'date_creation', 'statut'
    ]
    list_filter = ['type_document', 'statut', 'formation', 'date_creation']
    search_fields = ['numero_diplome', 'nom', 'prenom', 'telephone', 'email']
    readonly_fields = ['numero_diplome', 'date_creation', 'date_modification']
    
    fieldsets = (
        ('Identité du bénéficiaire', {
            'fields': ('nom', 'prenom', 'telephone', 'email', 'etudiant')
        }),
        ('Informations du document', {
            'fields': ('type_document', 'formation', 'numero_diplome', 'statut')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_delivrance', 'date_modification'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marquer_comme_delivre', 'marquer_comme_pret']
    
    def marquer_comme_delivre(self, request, queryset):
        queryset.update(statut='delivre')
        from django.utils import timezone
        for diplome in queryset:
            if not diplome.date_delivrance:
                diplome.date_delivrance = timezone.now().date()
                diplome.save()
        self.message_user(request, f"{queryset.count()} diplôme(s) marqué(s) comme délivré(s)")
    marquer_comme_delivre.short_description = "Marquer comme délivré"
    
    def marquer_comme_pret(self, request, queryset):
        queryset.update(statut='pret')
        self.message_user(request, f"{queryset.count()} diplôme(s) marqué(s) comme prêt(s)")
    marquer_comme_pret.short_description = "Marquer comme prêt"