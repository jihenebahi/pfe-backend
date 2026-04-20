# marketing_mail/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class MarketingEmail(models.Model):
    """
    Représente un email marketing envoyé depuis le CRM.
    Peut être envoyé soit à une adresse directe, soit à un segment de contacts.
    """

    SEND_MODE_CHOICES = [
        ('direct',  'Adresse e-mail directe'),
        ('segment', 'Segment de contacts'),
    ]

    GROUPE_CHOICES = [
        ('Prospects', 'Prospects'),
        ('Étudiants', 'Étudiants'),
        ('Diplômés',  'Diplômés'),
    ]

    # ── Expéditeur ────────────────────────────────────────────────────────────
    envoye_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='emails_marketing',
        verbose_name="Envoyé par",
        help_text="Utilisateur connecté qui a envoyé l'email"
    )

    # ── Contenu ───────────────────────────────────────────────────────────────
    objet   = models.CharField(max_length=255, verbose_name="Ligne d'objet")
    apercu  = models.CharField(max_length=255, blank=True, verbose_name="Texte d'aperçu")
    message = models.TextField(verbose_name="Corps du message")
    fichier = models.FileField(
        upload_to='marketing_mail/pieces_jointes/%Y/%m/',
        blank=True, null=True,
        verbose_name="Pièce jointe"
    )

    # ── Mode d'envoi ──────────────────────────────────────────────────────────
    send_mode = models.CharField(
        max_length=10,
        choices=SEND_MODE_CHOICES,
        default='segment',
        verbose_name="Mode d'envoi"
    )

    # Mode direct : une seule adresse email saisie manuellement
    email_direct = models.EmailField(
        blank=True,
        verbose_name="Adresse e-mail directe"
    )

    # Mode segment : groupe cible (Prospects / Étudiants / Diplômés)
    groupe = models.CharField(
        max_length=20,
        choices=GROUPE_CHOICES,
        blank=True,
        verbose_name="Groupe cible"
    )

    # ── Filtres de segment ────────────────────────────────────────────────────
    # Formations ciblées (Prospects, Étudiants, Diplômés)
    formations_cibles = models.ManyToManyField(
        'formation.Formation',
        blank=True,
        related_name='emails_marketing',
        verbose_name="Formations ciblées"
    )

    # Statuts prospects ciblés (uniquement quand groupe = Prospects)
    statuts_prospects = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Statuts prospects ciblés",
        help_text="Ex: ['nouveau', 'contacte', 'interesse']"
    )

    # Sources / réseaux sociaux ciblés (uniquement quand groupe = Prospects)
    sources_prospects = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Sources prospects ciblées",
        help_text="Ex: ['facebook', 'instagram', 'linkedin']"
    )

    # ── Statistiques ──────────────────────────────────────────────────────────
    nombre_destinataires = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de destinataires",
        help_text="Calculé au moment de l'envoi"
    )

    # ── Archivage ─────────────────────────────────────────────────────────────
    est_archive = models.BooleanField(default=False, verbose_name="Archivé")

    # ── Dates ─────────────────────────────────────────────────────────────────
    date_envoi      = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        ordering            = ['-date_envoi']
        verbose_name        = "Email Marketing"
        verbose_name_plural = "Emails Marketing"
        db_table            = 'marketing_emails'

    def __str__(self):
        groupe_info = self.email_direct if self.send_mode == 'direct' else self.groupe
        return f"{self.objet} → {groupe_info} ({self.date_envoi.strftime('%d/%m/%Y')})"

    @property
    def groupe_display(self):
        """Retourne le libellé du groupe ou l'email direct selon le mode."""
        if self.send_mode == 'direct':
            return self.email_direct
        return dict(self.GROUPE_CHOICES).get(self.groupe, self.groupe)


class DestinatairEmail(models.Model):
    """
    Trace chaque destinataire d'un email marketing.
    Permet de savoir exactement qui a reçu quel email.
    """

    TYPE_CHOICES = [
        ('prospect', 'Prospect'),
        ('etudiant', 'Étudiant'),
        ('diplome',  'Diplômé'),
        ('direct',   'Email direct'),
    ]

    email_marketing = models.ForeignKey(
        MarketingEmail,
        on_delete=models.CASCADE,
        related_name='destinataires',
        verbose_name="Email marketing"
    )

    # Références optionnelles selon le type
    prospect = models.ForeignKey(
        'prospects.Prospect',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='emails_recus',
        verbose_name="Prospect"
    )
    etudiant = models.ForeignKey(
        'etudiants.Etudiant',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='emails_recus',
        verbose_name="Étudiant"
    )
    diplome = models.ForeignKey(
        'diplomes.Diplome',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='emails_recus',
        verbose_name="Diplômé"
    )

    # Email effectivement utilisé (dénormalisé pour l'historique)
    email_adresse = models.EmailField(verbose_name="Adresse email")
    type_destinataire = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name="Type de destinataire"
    )

    date_envoi = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")

    class Meta:
        ordering            = ['-date_envoi']
        verbose_name        = "Destinataire Email"
        verbose_name_plural = "Destinataires Emails"
        db_table            = 'marketing_email_destinataires'

    def __str__(self):
        return f"{self.email_adresse} ← {self.email_marketing.objet}"