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
        ('certifie',   'Certifié'),
    ]

    # Formations (plusieurs possibles, comme pour le prospect)
    formations_suivies = models.ManyToManyField(
        Formation,
        related_name='etudiants',
        blank=True,
        help_text="Formations suivies par l'étudiant"
    )

    date_inscription = models.DateField(auto_now_add=True)
    statut           = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    responsable      = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etudiants_suivis'
    )
    notes            = models.TextField(blank=True)

    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering           = ['-date_inscription']
        verbose_name       = "Étudiant"
        verbose_name_plural = "Étudiants"

    @property
    def formations_noms(self):
        return ", ".join([f.intitule for f in self.formations_suivies.all()])

    @property
    def solde_restant(self):
        """Calcule la somme restante à payer sur tous les paiements"""
        total = sum(p.montant_total for p in self.paiements.all())
        paye  = sum(p.montant_paye  for p in self.paiements.all())
        return total - paye


class Document(models.Model):
    """Documents fournis par l'étudiant (CIN, CV, Contrat, Reçu, RNE, Autre)"""

    TYPE_CHOICES = [
        ('cin',      'CIN'),
        ('cv',       'CV'),
        ('contrat',  'Contrat'),
        ('recu',     'Reçu'),
        ('rne',      'RNE'),
        ('autre',    'Autre'),
    ]

    etudiant     = models.ForeignKey(
        Etudiant, on_delete=models.CASCADE, related_name='documents'
    )
    type_document = models.CharField(max_length=20, choices=TYPE_CHOICES)
    fichier       = models.FileField(upload_to='etudiants/documents/%Y/%m/')
    date_upload   = models.DateTimeField(auto_now_add=True)
    commentaire   = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering           = ['-date_upload']
        verbose_name       = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return f"{self.get_type_document_display()} — {self.etudiant.nom_complet}"


class Paiement(models.Model):
    """Un versement effectué par l'étudiant"""

    MODE_CHOICES = [
        ('espece',   'Espèce'),
        ('cheque',   'Chèque'),
        ('virement', 'Virement'),
    ]

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('partiel',    'Partiel'),
        ('complet',    'Complet'),
    ]

    etudiant       = models.ForeignKey(
        Etudiant, on_delete=models.CASCADE, related_name='paiements'
    )
    montant_total  = models.DecimalField(max_digits=10, decimal_places=3)   # en TND
    montant_paye   = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    mode_paiement  = models.CharField(max_length=20, choices=MODE_CHOICES)
    statut         = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='en_attente'
    )
    date_paiement  = models.DateField()
    reference      = models.CharField(
        max_length=100, blank=True,
        help_text="N° chèque, référence virement, etc."
    )
    notes          = models.TextField(blank=True)
    enregistre_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    date_creation  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering           = ['-date_paiement']
        verbose_name       = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return (
            f"{self.etudiant.nom_complet} — "
            f"{self.montant_paye}/{self.montant_total} TND — "
            f"{self.get_statut_display()}"
        )

    @property
    def montant_restant(self):
        return self.montant_total - self.montant_paye

    def save(self, *args, **kwargs):
        """Met à jour le statut automatiquement selon les montants"""
        if self.montant_paye <= 0:
            self.statut = 'en_attente'
        elif self.montant_paye < self.montant_total:
            self.statut = 'partiel'
        else:
            self.statut = 'complet'
        super().save(*args, **kwargs)