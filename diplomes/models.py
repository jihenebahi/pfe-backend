# diplomes/models.py
from django.db import models
from formation.models import Formation


class Diplome(models.Model):
    """
    Snapshot d'un étudiant certifié pour une formation précise.
    Les données sont copiées au moment de la certification afin de
    conserver un historique même si l'étudiant est supprimé.
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
    formation           = models.ForeignKey(
        Formation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='diplomes',
        help_text="FK vers la formation (peut devenir null si la formation est supprimée)"
    )
    # Snapshot du libellé pour conserver l'historique même si Formation est supprimée
    formation_intitule  = models.CharField(max_length=255, blank=True)
    formation_duree     = models.CharField(max_length=50,  blank=True)

    date_attestation = models.DateField(help_text="Date figurant sur l'attestation")

    # ── Présences (optionnel) ────────────────────────────────────────
    seances_total = models.PositiveIntegerField(
        default=0,
        help_text="Nombre total de séances dans la formation"
    )
    absences = models.PositiveIntegerField(
        default=0,
        help_text="Nombre de séances manquées"
    )

    # ── Référence informelle à l'étudiant d'origine ──────────────────
    # Stocké comme entier simple (pas FK) car l'étudiant sera supprimé
    etudiant_id_origine = models.IntegerField(
        null=True, blank=True,
        help_text="ID de l'étudiant au moment de la certification (référence historique)"
    )

    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering           = ['-date_attestation', '-date_creation']
        verbose_name       = "Diplômé"
        verbose_name_plural = "Diplômés"
        # Unicité : un étudiant ne peut être certifié qu'une seule fois par formation
        unique_together = [['etudiant_id_origine', 'formation']]

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.formation_intitule}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @property
    def taux_presence(self):
        """Pourcentage de présence (0-100)."""
        if not self.seances_total:
            return 0
        presences = self.seances_total - self.absences
        return round((presences / self.seances_total) * 100)