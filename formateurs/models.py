from django.db import models
from django.core.validators import RegexValidator, FileExtensionValidator


class Formateur(models.Model):

    # ==============================
    # 🔹 INFORMATIONS PERSONNELLES
    # ==============================

    nom    = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    telephone = models.CharField(
        max_length=15,
        blank=True,
        default='',
        validators=[
            RegexValidator(
                regex=r'^(\+216)?[2459]\d{7}$',
                message="Le numéro doit être tunisien (ex: +21655123456 ou 55123456)"
            )
        ]
    )

    adresse = models.CharField(max_length=255, blank=True, default='')

    # ==============================
    # 🔹 INFORMATIONS PROFESSIONNELLES
    # ==============================

    specialites = models.TextField(help_text="Ex: Django, IA, Marketing Digital")

    NIVEAU_CHOICES = [
        ('junior',        'Junior'),
        ('universitaire', 'Universitaire'),
        ('expert',        'Expert'),
    ]
    niveau_intervention = models.CharField(max_length=20, choices=NIVEAU_CHOICES)

    TYPE_CONTRAT_CHOICES = [
        ('interne',  'Interne'),
        ('vacation', 'Vacation'),
    ]
    type_contrat = models.CharField(max_length=20, choices=TYPE_CONTRAT_CHOICES)



    # CV — fichier unique (inchangé)
    cv_pdf = models.FileField(
        upload_to='documents/formateurs/cv/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        blank=True,
        null=True
    )

    # ==============================
    # 🔹 SYSTEME
    # ==============================

    est_actif = models.BooleanField(default=True, editable=False)  # ✅ toujours True, non modifiable

    date_creation    = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"


# ✅ NOUVEAU : Contrats — plusieurs fichiers PDF par formateur
class ContratPDF(models.Model):
    formateur = models.ForeignKey(
        Formateur,
        on_delete=models.CASCADE,
        related_name='contrats'
    )
    fichier = models.FileField(
        upload_to='documents/formateurs/contrats/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contrat de {self.formateur} — {self.fichier.name}"


# ✅ NOUVEAU : Diplômes — plusieurs fichiers PDF par formateur
class DiplomePDF(models.Model):
    formateur = models.ForeignKey(
        Formateur,
        on_delete=models.CASCADE,
        related_name='diplomes'
    )
    fichier = models.FileField(
        upload_to='documents/formateurs/diplomes/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diplôme de {self.formateur} — {self.fichier.name}"