# etudiants/models.py
from django.db import models
from django.contrib.auth import get_user_model
from core.models import PersonneBase
from formation.models import Formation

User = get_user_model()


class Etudiant(PersonneBase):
    """
    Hérite automatiquement de PersonneBase :
      nom, prenom, email, telephone, ville, pays,
      date_naissance, genre, niveau_etudes, diplome_obtenu
    """

    STATUT_CHOICES = [
        ('actif',      'Actif'),
        ('abandonne',  'Abandonné'),
    ]

    MODE_PAIEMENT_CHOICES = [
        ('espece',   'Espèce'),
        ('cheque',   'Chèque'),
        ('virement', 'Virement'),
    ]

    # Formations (plusieurs possibles) — via through model EtudiantFormation
    formations_suivies = models.ManyToManyField(
        Formation,
        through='EtudiantFormation',
        related_name='etudiants',
        blank=True,
        help_text="Formations suivies par l'étudiant"
    )

    date_inscription  = models.DateField(auto_now_add=True)
    statut            = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    responsable       = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etudiants_suivis'
    )
    notes             = models.TextField(blank=True)

    mode_paiement = models.CharField(
        max_length=20,
        choices=MODE_PAIEMENT_CHOICES,
        default='espece',
    )

    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering            = ['-date_inscription', '-date_creation']  # ← ajouter date_creation
        verbose_name        = "Étudiant"
        verbose_name_plural = "Étudiants"

    def __str__(self):
        return f"{self.nom_complet} ({self.get_statut_display()})"

    @property
    def formations_noms(self):
        return ", ".join([f.intitule for f in self.formations_suivies.all()])

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


class EtudiantFormation(models.Model):
    """
    Table de liaison Etudiant ↔ Formation avec champs complémentaires :
    - date d'inscription spécifique à chaque formation
    - statut d'attestation par formation
    """
    etudiant  = models.ForeignKey(
        Etudiant, on_delete=models.CASCADE,
        related_name='etudiant_formations'
    )
    formation = models.ForeignKey(
        Formation, on_delete=models.CASCADE,
        related_name='etudiant_formations'
    )

    date_inscription_formation = models.DateField(auto_now_add=True)

    attestation      = models.BooleanField(default=False)
    date_attestation = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ['etudiant', 'formation']
        ordering        = ['date_inscription_formation']
        verbose_name        = "Inscription formation"
        verbose_name_plural = "Inscriptions formations"

    def __str__(self):
        return f"{self.etudiant.nom_complet} → {self.formation.intitule}"


class Document(models.Model):
    """
    Documents fournis par l'étudiant (CIN, CV, Contrat, Reçu, RNE, Autre).
    """
    TYPE_CHOICES = [
        ('cin',     'CIN'),
        ('cv',      'CV'),
        ('contrat', 'Contrat'),
        ('recu',    'Reçu'),
        ('rne',     'RNE'),
        ('autre',   'Autre'),
    ]

    etudiant      = models.ForeignKey(
        Etudiant, on_delete=models.CASCADE, related_name='documents'
    )
    type_document = models.CharField(max_length=20, choices=TYPE_CHOICES,
                                     verbose_name="Type de document")
    fichier       = models.FileField(
        upload_to='etudiants/documents/%Y/%m/',
        blank=True, null=True,
        verbose_name="Fichier (optionnel)"
    )
    date_upload   = models.DateTimeField(auto_now_add=True)
    commentaire   = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering            = ['-date_upload']
        verbose_name        = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return f"{self.get_type_document_display()} — {self.etudiant.nom_complet}"