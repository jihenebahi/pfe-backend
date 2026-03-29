# prospects/models.py
from django.db import models
from django.contrib.auth import get_user_model
from formation.models import Formation
from core.models import PersonneBase   # ← import de la base
from datetime import date   # ← ajouter cet import en haut du fichier si absent


User = get_user_model()

class Prospect(PersonneBase):   # ← hérite de PersonneBase
    """
    Hérite de PersonneBase :
      nom, prenom, email, telephone, ville, pays,
      date_naissance, genre, niveau_etudes, diplome_obtenu
    """

    SOURCE_CHOICES = [
        ('facebook',       'Facebook'),
        ('instagram',      'Instagram'),
        ('tiktok',         'TikTok'),
        ('linkedin',       'LinkedIn'),
        ('google',         'Google'),
        ('site_web',       'Site web'),
        ('recommandation', 'Recommandation'),
        ('appel_entrant',  'Appel entrant'),
        ('autre',          'Autre'),
    ]

    NIVEAU_CHOICES = [
        ('debutant',      'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance',        'Avancé'),
    ]

    MODE_CHOICES = [
        ('presentiel', 'Présentiel'),
        ('en_ligne',   'En ligne'),
        ('hybride',    'Hybride'),
    ]

    CANAL_CHOICES = [
        ('telephone', 'Téléphone'),
        ('email',     'Email'),
        ('whatsapp',  'WhatsApp'),
    ]

    STATUT_CHOICES = [
        ('nouveau',   'Nouveau'),
        ('contacte',  'Contacté'),
        ('interesse', 'Intéressé'),
        ('converti',  'Converti'),
        ('perdu',     'Perdu'),
    ]

    # Champs spécifiques au prospect
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)

    formations_souhaitees = models.ManyToManyField(
        Formation,
        related_name='prospects',
        blank=True,
    )

    niveau_estime         = models.CharField(max_length=20, choices=NIVEAU_CHOICES)
    mode_prefere          = models.CharField(max_length=20, choices=MODE_CHOICES)
    canal_contact_prefere = models.CharField(max_length=20, choices=CANAL_CHOICES, blank=True)
    commentaires          = models.TextField(blank=True)

    statut      = models.CharField(max_length=20, choices=STATUT_CHOICES)
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='prospects_suivis'
    )

    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    ip_address        = models.GenericIPAddressField(blank=True, null=True)
    user_agent        = models.TextField(blank=True)

    class Meta:
        ordering            = ['-date_creation']
        verbose_name        = "Prospect"
        verbose_name_plural = "Prospects"

    @property
    def formations_noms(self):
        return ", ".join([f.intitule for f in self.formations_souhaitees.all()])


class HistoriqueEchange(models.Model):
    TYPE_ECHANGE_CHOICES = [
        ('appel',   'Appel téléphonique'),
        ('email',   'Email'),
        ('rdv',     'Rendez-vous'),
        ('message', 'Message WhatsApp'),
        ('autre',   'Autre'),
    ]

    prospect     = models.ForeignKey(Prospect, on_delete=models.CASCADE, related_name='historiques')
    type_echange = models.CharField(max_length=20, choices=TYPE_ECHANGE_CHOICES)
    date_echange = models.DateTimeField(auto_now_add=True)
    utilisateur  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    contenu      = models.TextField()
    notes        = models.TextField(blank=True)

    class Meta:
        ordering            = ['-date_echange']
        verbose_name        = "Historique d'échange"
        verbose_name_plural = "Historiques d'échanges"

    def __str__(self):
        return f"{self.get_type_echange_display()} - {self.date_echange.strftime('%d/%m/%Y %H:%M')}"
    
# ──────────────────────────────────────────────────────────────────────────────
#  À AJOUTER à la fin de  prospects/models.py
#  (après la classe HistoriqueEchange)
# ──────────────────────────────────────────────────────────────────────────────



class Relance(models.Model):
    """
    Représente une relance programmée pour un prospect.
    Le statut est CALCULÉ automatiquement à partir de la date,
    sauf si la relance a été marquée 'fait'.
    """

    STATUT_CHOICES = [
        ('a_venir',     'À venir'),
        ('aujourd_hui', "Aujourd'hui"),
        ('en_retard',   'En retard'),
        ('fait',        'Fait'),
    ]

    prospect     = models.ForeignKey(
        Prospect, on_delete=models.CASCADE, related_name='relances'
    )
    date_relance = models.DateField()
    commentaire  = models.TextField(blank=True)

    # Statut persisté — mis à jour à chaque action « OK »
    statut       = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='a_venir'
    )

    # Rempli quand l'assistante clique « OK »
    date_action  = models.DateTimeField(null=True, blank=True)

    created_by   = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='relances_creees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['date_relance']
        verbose_name        = "Relance"
        verbose_name_plural = "Relances"

    def __str__(self):
        return f"Relance {self.prospect} — {self.date_relance}"

    # ── Statut calculé à la volée ──────────────────────────────────────────
    @property
    def statut_calcule(self):
        """
        Priorité :
          1. 'fait'         → toujours 'fait'
          2. date < today   → 'en_retard'
          3. date = today   → 'aujourd_hui'
          4. date > today   → 'a_venir'
        """
        if self.statut == 'fait':
            return 'fait'
        today = date.today()
        if self.date_relance < today:
            return 'en_retard'
        if self.date_relance == today:
            return 'aujourd_hui'
        return 'a_venir'