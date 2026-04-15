# diplomes/models.py 
from django.db import models
from django.contrib.auth import get_user_model
from formation.models import Formation
from datetime import date

User = get_user_model()


class Diplome(models.Model):
    """
    Snapshot d'un étudiant certifié pour une formation précise.
    """

    # ── Snapshot identité ────────────────────────────────────────────
    nom       = models.CharField(max_length=100)
    prenom    = models.CharField(max_length=100)
    email     = models.EmailField(blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    ville     = models.CharField(max_length=100, blank=True)
    pays      = models.CharField(max_length=50, blank=True)
    notes     = models.TextField(blank=True)

    # ── Formation certifiée ──────────────────────────────────────────
    formation = models.ForeignKey(
        Formation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='diplomes',
    )

    formation_intitule = models.CharField(max_length=255, blank=True)
    formation_duree    = models.CharField(max_length=50, blank=True)

    date_attestation = models.DateField()

    # ── Présences ────────────────────────────────────────────────────
    seances_total = models.PositiveIntegerField(default=0)
    absences      = models.PositiveIntegerField(default=0)

    # ── Référence historique ─────────────────────────────────────────
    etudiant_id_origine = models.IntegerField(null=True, blank=True)

    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_attestation', '-date_creation']
        verbose_name = "Diplômé"
        verbose_name_plural = "Diplômés"
        unique_together = [['etudiant_id_origine', 'formation']]

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.formation_intitule}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @property
    def taux_presence(self):
        if not self.seances_total:
            return 0
        presences = self.seances_total - self.absences
        return round((presences / self.seances_total) * 100)


# ──────────────────────────────────────────────────────────────────────────────
#  NOUVEAU : Relances pour les diplômés
# ──────────────────────────────────────────────────────────────────────────────
# diplomes/models.py

class DiplomeRelance(models.Model):
    """
    Représente une relance programmée pour un diplômé.
    """

    STATUT_CHOICES = [
        ('a_venir',     'À venir'),
        ('aujourd_hui', "Aujourd'hui"),
        ('en_retard',   'En retard'),
        ('fait',        'Fait'),
    ]

    diplome = models.ForeignKey(
        Diplome,
        on_delete=models.CASCADE,
        related_name='relances'
    )
    formation = models.ForeignKey(
        'formation.Formation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relances_diplomes'
    )
    date_relance = models.DateField()
    commentaire = models.TextField(blank=True)

    # Statut persisté
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='a_venir'
    )

    # Rempli quand l'utilisateur clique « OK »
    date_action = models.DateTimeField(null=True, blank=True)
    
    # NOUVEAU : Notes saisies lors de l'appel effectué
    notes_action = models.TextField(blank=True, default='')

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='relances_diplomes_creees'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_relance']
        verbose_name = "Relance diplômé"
        verbose_name_plural = "Relances diplômés"

    def __str__(self):
        return f"Relance {self.diplome} — {self.date_relance}"

    @property
    def statut_calcule(self):
        if self.statut == 'fait':
            return 'fait'
        today = date.today()
        if self.date_relance < today:
            return 'en_retard'
        if self.date_relance == today:
            return 'aujourd_hui'
        return 'a_venir'