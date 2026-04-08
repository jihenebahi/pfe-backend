from django.db import models
from django.core.validators import EmailValidator
from formation.models import Formation
from etudiants.models import Etudiant

class Diplome(models.Model):
    """
    Modèle pour gérer les attestations/diplômes délivrés aux étudiants
    """
    
    TYPEDOC_CHOICES = [
        ('attestation_reussite', 'Attestation de Réussite'),
        ('diplome', 'Diplôme'),
        ('certificat', 'Certificat de Formation'),
    ]
    
    # Informations de l'étudiant (dénormalisées pour conserver l'historique)
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    telephone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(
        blank=True,
        default='',
        validators=[EmailValidator()],
        verbose_name="Email"
    )
    
    # Référence à l'étudiant (optionnelle, garde le lien)
    etudiant = models.ForeignKey(
        Etudiant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diplomes',
        verbose_name="Étudiant lié",
        help_text="L'étudiant concerné (optionnel pour l'historique)"
    )
    
    # Formation
    formation = models.ForeignKey(
        Formation,
        on_delete=models.PROTECT,
        related_name='diplomes',
        verbose_name="Formation",
        help_text="Formation suivie avec succès"
    )
    
    # Type de document
    type_document = models.CharField(
        max_length=30,
        choices=TYPEDOC_CHOICES,
        default='attestation_reussite',
        verbose_name="Type de document"
    )
    
    # Dates
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_delivrance = models.DateField(null=True, blank=True, verbose_name="Date de délivrance")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    
    # Métadonnées
    numero_diplome = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="Numéro de diplôme",
        help_text="Numéro unique généré automatiquement"
    )
    
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    # Statut
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('pret', 'Prêt à délivrer'),
        ('delivre', 'Délivré'),
        ('annule', 'Annulé'),
    ]
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name="Statut"
    )
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Diplôme / Attestation"
        verbose_name_plural = "Diplômes / Attestations"
    
    def save(self, *args, **kwargs):
        # Générer automatiquement le numéro de diplôme si non défini
        if not self.numero_diplome:
            import datetime
            year = datetime.datetime.now().year
            # Compter les diplômes existants pour l'année
            count = Diplome.objects.filter(
                date_creation__year=year
            ).count() + 1
            prefix = 'DIP' if self.type_document == 'diplome' else 'ATT'
            self.numero_diplome = f"{prefix}{year}{count:05d}"
        
        # Si date_delivrance non définie, mettre la date actuelle
        if self.statut == 'delivre' and not self.date_delivrance:
            from django.utils import timezone
            self.date_delivrance = timezone.now().date()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        type_str = dict(self.TYPEDOC_CHOICES).get(self.type_document, 'Document')
        return f"{type_str} - {self.prenom} {self.nom} - {self.formation.intitule}"
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"
    
    @property
    def type_document_label(self):
        return dict(self.TYPEDOC_CHOICES).get(self.type_document, '')