from django.db import models
from django.core.validators import RegexValidator, FileExtensionValidator


class Formateur(models.Model):

    # ==============================
    # 🔹 INFORMATIONS PERSONNELLES
    # ==============================

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    telephone = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^(\\+216)?[2459]\\d{7}$',
                message="Le numéro doit être tunisien (ex: +21612345678 ou 12345678)"
            )
        ]
    )

    adresse = models.CharField(max_length=255)

    # ==============================
    # 🔹 INFORMATIONS PROFESSIONNELLES
    # ==============================

    specialites = models.TextField(help_text="Ex: Django, IA, Marketing Digital")

    NIVEAU_CHOICES = [
        ('junior', 'Junior'),
        ('universitaire', 'Universitaire'),
        ('expert', 'Expert'),
    ]

    niveau_intervention = models.CharField(
        max_length=20,
        choices=NIVEAU_CHOICES
    )

    TYPE_CONTRAT_CHOICES = [
        ('interne', 'Interne'),
        ('vacation', 'Vacation'),
    ]

    type_contrat = models.CharField(
        max_length=20,
        choices=TYPE_CONTRAT_CHOICES
    )

    disponibilites = models.TextField(
        help_text="Ex: Lundi-Vendredi 18h-21h"
    )

    # ==============================
    # 🔹 SUIVI
    # ==============================

    heures_realisees = models.PositiveIntegerField(default=0)

    contrat_pdf = models.FileField(
        upload_to='documents/formateurs/contrats/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        blank=True,
        null=True
    )

    cv_pdf = models.FileField(
        upload_to='documents/formateurs/cv/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        blank=True,
        null=True
    )

    diplomes_pdf = models.FileField(
        upload_to='documents/formateurs/diplomes/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        blank=True,
        null=True
    )

    # ==============================
    # 🔹 SYSTEME
    # ==============================

    est_actif = models.BooleanField(default=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"