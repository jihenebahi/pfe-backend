# marketing_mail/admin.py

from django.contrib import admin
from .models import MarketingEmail, DestinatairEmail


class DestinatairEmailInline(admin.TabularInline):
    model        = DestinatairEmail
    extra        = 0
    readonly_fields = ('email_adresse', 'type_destinataire', 'prospect', 'etudiant', 'diplome', 'date_envoi')
    can_delete   = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(MarketingEmail)
class MarketingEmailAdmin(admin.ModelAdmin):
    list_display  = (
        'objet', 'envoye_par', 'send_mode', 'groupe_display',
        'nombre_destinataires', 'est_archive', 'date_envoi'
    )
    list_filter   = ('send_mode', 'groupe', 'est_archive', 'date_envoi')
    search_fields = ('objet', 'apercu', 'email_direct', 'envoye_par__username', 'envoye_par__email')
    readonly_fields = ('date_envoi', 'date_modification', 'nombre_destinataires')
    filter_horizontal = ('formations_cibles',)
    date_hierarchy = 'date_envoi'
    inlines       = [DestinatairEmailInline]

    fieldsets = (
        ("Expéditeur", {
            'fields': ('envoye_par',)
        }),
        ("Contenu", {
            'fields': ('objet', 'apercu', 'message', 'fichier')
        }),
        ("Destinataires", {
            'fields': ('send_mode', 'email_direct', 'groupe',
                       'formations_cibles', 'statuts_prospects', 'sources_prospects')
        }),
        ("Statistiques & Statut", {
            'fields': ('nombre_destinataires', 'est_archive', 'date_envoi', 'date_modification')
        }),
    )

    def groupe_display(self, obj):
        return obj.groupe_display
    groupe_display.short_description = "Groupe / Email cible"


@admin.register(DestinatairEmail)
class DestinatairEmailAdmin(admin.ModelAdmin):
    list_display  = ('email_adresse', 'type_destinataire', 'email_marketing', 'date_envoi')
    list_filter   = ('type_destinataire', 'date_envoi')
    search_fields = ('email_adresse', 'email_marketing__objet')
    readonly_fields = ('date_envoi',)