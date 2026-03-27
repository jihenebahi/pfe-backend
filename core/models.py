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

    # Champs communs
    nom      = models.CharField(max_length=100)
    prenom   = models.CharField(max_length=100)
    email    = models.EmailField(validators=[EmailValidator()])
    telephone = models.CharField(max_length=20, unique=True)
    ville    = models.CharField(max_length=100)
    pays     = models.CharField(max_length=50, choices=PAYS_CHOICES)

    # Nouveaux champs demandés par le centre
    date_naissance  = models.DateField(null=True, blank=True)
    genre           = models.CharField(max_length=10, choices=GENRE_CHOICES, blank=True)
    niveau_etudes   = models.CharField(max_length=20, choices=NIVEAU_ETUDES_CHOICES, blank=True)
    diplome_obtenu  = models.CharField(max_length=20, choices=DIPLOME_CHOICES, blank=True)

    class Meta:
        abstract = True   # ← clé : pas de table créée pour cette classe

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.email}"