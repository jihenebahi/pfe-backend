# core/models.py
from django.db import models
from django.core.validators import EmailValidator

class PersonneBase(models.Model):
    """Classe abstraite partagée entre Prospect et Etudiant"""

    PAYS_CHOICES = [
        ('tunisie',  'Tunisie'),
        ('france',   'France'),
        ('algerie',  'Algérie'),
        ('maroc',    'Maroc'),
        ('belgique', 'Belgique'),
        ('canada',   'Canada'),
        ('autre',    'Autre'),
    ]

    GENRE_CHOICES = [
        ('homme', 'Homme'),
        ('femme', 'Femme'),
        ('autre', 'Autre'),
    ]

    NIVEAU_ETUDES_CHOICES = [
        ('primaire',       'Primaire'),
        ('preparatoire',   'Préparatoire'),
        ('secondaire',     'Secondaire'),
        ('universitaire',  'Universitaire'),
    ]

    DIPLOME_CHOICES = [
        ('bac',     'Bac'),
        ('licence', 'Licence'),
        ('master',  'Master'),
        ('autre',   'Autre'),
    ]

    nom       = models.CharField(max_length=100)
    prenom    = models.CharField(max_length=100)

    # ✅ MODIFIÉ : blank=True → le champ est optionnel dans les formulaires et l'API.
    # On garde validators=[EmailValidator()] pour s'assurer que si une valeur
    # est fournie, elle respecte bien le format email.
    email     = models.EmailField(
        blank=True,
        default='',
        validators=[EmailValidator()],
    )

    telephone = models.CharField(max_length=20, unique=True)
    ville     = models.CharField(max_length=100)
    pays      = models.CharField(max_length=50, choices=PAYS_CHOICES)

    date_naissance  = models.DateField(null=True, blank=True)
    genre           = models.CharField(max_length=10, choices=GENRE_CHOICES, blank=True)
    niveau_etudes   = models.CharField(max_length=20, choices=NIVEAU_ETUDES_CHOICES, blank=True)
    diplome_obtenu  = models.CharField(max_length=20, choices=DIPLOME_CHOICES, blank=True)

    class Meta:
        abstract = True

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    def __str__(self):
        # ✅ MODIFIÉ : on affiche le téléphone si l'email est absent
        contact = self.email if self.email else self.telephone
        return f"{self.prenom} {self.nom} - {contact}"