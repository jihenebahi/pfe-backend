# prospects/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Prospect, HistoriqueEchange

class HistoriqueEchangeInline(admin.TabularInline):
    model = HistoriqueEchange
    extra = 1
    fields = ['type_echange', 'date_echange', 'utilisateur', 'contenu']
    readonly_fields = ['date_echange']


@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'email', 'telephone', 'formations_courtes', 
                    'statut_colore', 'source', 'responsable', 'date_creation']
    list_filter = ['statut', 'source', 'type_prospect', 'pays', 'responsable', 'formations_souhaitees']
    search_fields = ['nom', 'prenom', 'email', 'telephone']
    filter_horizontal = ['formations_souhaitees']  # ✅ Interface agréable pour ManyToMany
    inlines = [HistoriqueEchangeInline]
    readonly_fields = ['date_creation', 'date_modification', 'ip_address', 'user_agent', 'formations_list']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'email', 'telephone', 'ville', 'pays')
        }),
        ('Informations commerciales', {
            'fields': ('source', 'type_prospect', 'service_recherche', 
                      'formations_souhaitees', 'niveau_estime', 'mode_prefere',
                      'disponibilite', 'canal_contact_prefere', 'commentaires')
        }),
        ('Suivi', {
            'fields': ('statut', 'responsable', 'date_creation', 'date_modification')
        }),
        ('Métadonnées', {
            'classes': ('collapse',),
            'fields': ('ip_address', 'user_agent', 'formations_list')
        }),
    )
    
    def formations_courtes(self, obj):
        """Affiche un résumé des formations dans la liste"""
        formations = obj.formations_souhaitees.all()[:3]
        if formations:
            noms = [f.intitule[:20] + '...' if len(f.intitule) > 20 else f.intitule for f in formations]
            result = ", ".join(noms)
            if obj.formations_souhaitees.count() > 3:
                result += f" et {obj.formations_souhaitees.count() - 3} autre(s)"
            return result
        return "-"
    formations_courtes.short_description = 'Formations'
    
    def formations_list(self, obj):
        """Affiche la liste complète des formations en lecture seule"""
        formations = obj.formations_souhaitees.all()
        if formations:
            return format_html("<br>".join([f"- {f.intitule}" for f in formations]))
        return "Aucune formation sélectionnée"
    formations_list.short_description = 'Liste des formations'
    
    def statut_colore(self, obj):
        colors = {
            'nouveau': '#33CCFF',
            'contacte': '#FFCC33',
            'en_cours': '#336699',
            'qualifie': '#1A6B4A',
            'converti': '#27ae60',
            'perdu': '#e53e3e',
        }
        color = colors.get(obj.statut, '#333')
        return format_html(
            '<span style="background: {}10; color: {}; padding: 3px 8px; border-radius: 12px; font-weight: 500;">{}</span>',
            color, color, obj.get_statut_display()
        )
    statut_colore.short_description = 'Statut'
    
    def nom_complet(self, obj):
        return f"{obj.prenom} {obj.nom}"
    nom_complet.short_description = 'Nom complet'


@admin.register(HistoriqueEchange)
class HistoriqueEchangeAdmin(admin.ModelAdmin):
    list_display = ['prospect', 'type_echange', 'date_echange', 'utilisateur']
    list_filter = ['type_echange', 'date_echange']
    search_fields = ['prospect__nom', 'prospect__prenom', 'contenu']
    readonly_fields = ['date_echange']