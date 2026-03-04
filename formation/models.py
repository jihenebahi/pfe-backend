# models.py
from django.db import models

class Formation(models.Model):

    NIVEAU_CHOICES = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    ]

    FORMAT_CHOICES = [
        ('presentiel', 'Présentiel'),
        ('en_ligne', 'En ligne'),
        ('hybride', 'Hybride'),
    ]

    intitule = models.CharField(max_length=255)

    # 🔥 AJOUT DE LA CATEGORIE ICI
    categorie = models.ForeignKey(
        'categories.Categorie',   # nom_app.NomModel
        on_delete=models.CASCADE,
        related_name='formations'
    )

    formateurs = models.ManyToManyField(
    'formateurs.Formateur',
    related_name='formations',
    blank=True
    )

    description = models.TextField()
    objectifs_pedagogiques = models.TextField()
    prerequis = models.TextField(blank=True, null=True)

    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES)
    duree = models.PositiveIntegerField(help_text="Durée totale en heures")

    format = models.CharField(max_length=20, choices=FORMAT_CHOICES)

    date_debut = models.DateField()
    date_fin = models.DateField()

    prix_ht = models.DecimalField(max_digits=10, decimal_places=2)
    prix_ttc = models.DecimalField(max_digits=10, decimal_places=2)
    
    # ✅ NOUVEAU CHAMP : Nombre de tranches de paiement
    nb_tranches_paiement = models.PositiveIntegerField(
        default=1,
        help_text="Nombre de tranches pour le paiement (1 = paiement unique)"
    )

    est_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.intitule