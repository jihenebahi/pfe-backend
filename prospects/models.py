# prospects/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, EmailValidator
from formation.models import Formation  # Import du modèle Formation existant

User = get_user_model()

class Prospect(models.Model):
    # Types de prospect
    TYPE_PROSPECT_CHOICES = [
        ('particulier', 'Particulier'),
        ('entreprise', 'Entreprise'),
    ]
    
    # Services recherchés
    SERVICE_CHOICES = [
        ('formation', 'Formation'),
        ('consulting', 'Consulting'),
        ('les_deux', 'Les deux'),
    ]
    
    # Sources
    SOURCE_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('linkedin', 'LinkedIn'),
        ('google', 'Google'),
        ('site_web', 'Site web'),
        ('recommandation', 'Recommandation'),
        ('appel_entrant', 'Appel entrant'),
        ('autre', 'Autre'),
    ]
    
    # Niveaux
    NIVEAU_CHOICES = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    ]
    
    # Modes préférés
    MODE_CHOICES = [
        ('presentiel', 'Présentiel'),
        ('en_ligne', 'En ligne'),
        ('hybride', 'Hybride'),
    ]
    
    # Canaux de contact
    CANAL_CHOICES = [
        ('telephone', 'Téléphone'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    # Statuts
    STATUT_CHOICES = [
        ('nouveau', 'Nouveau'),
        ('contacte', 'Contacté'),
        ('en_cours', 'En cours'),
        ('qualifie', 'Qualifié'),
        ('converti', 'Converti'),
        ('perdu', 'Perdu'),
    ]
    
    # Pays
    PAYS_CHOICES = [
        ('tunisie', 'Tunisie'),
        ('france', 'France'),
        ('algerie', 'Algérie'),
        ('maroc', 'Maroc'),
        ('belgique', 'Belgique'),
        ('canada', 'Canada'),
        ('autre', 'Autre'),
    ]
    
    # Informations personnelles
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()])
    telephone = models.CharField(max_length=20)          # ✅ supprimé le validator regex (géré côté React)
    ville = models.CharField(max_length=100)             # ✅ obligatoire → supprimé blank=True
    pays = models.CharField(max_length=50, choices=PAYS_CHOICES)              # ✅ supprimé default
    
    # Informations commerciales
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)          # ✅ supprimé default
    type_prospect = models.CharField(max_length=20, choices=TYPE_PROSPECT_CHOICES)   # ✅ supprimé default
    service_recherche = models.CharField(max_length=20, choices=SERVICE_CHOICES)     # ✅ supprimé default
    
    # Plusieurs formations possibles (ManyToMany)
    formations_souhaitees = models.ManyToManyField(
        Formation,
        related_name='prospects',
        blank=True,
        help_text="Formations souhaitées par le prospect"
    )
    
    niveau_estime = models.CharField(max_length=20, choices=NIVEAU_CHOICES)   # ✅ supprimé default
    mode_prefere = models.CharField(max_length=20, choices=MODE_CHOICES)      # ✅ supprimé default
    disponibilite = models.CharField(max_length=200, blank=True, help_text="Dates, horaires de disponibilité")  # optionnel
    canal_contact_prefere = models.CharField(max_length=20, choices=CANAL_CHOICES, blank=True)  # optionnel → blank=True
    commentaires = models.TextField(blank=True)          # optionnel
    
    # Suivi du prospect
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES)          # ✅ supprimé default
    responsable = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='prospects_suivis'
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    # Métadonnées
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Prospect"
        verbose_name_plural = "Prospects"
    
    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.email}"
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"
    
    @property
    def formations_list(self):
        """Retourne la liste des formations souhaitées"""
        return self.formations_souhaitees.all()
    
    @property
    def formations_noms(self):
        """Retourne les noms des formations séparés par des virgules"""
        return ", ".join([f.intitule for f in self.formations_souhaitees.all()])


class HistoriqueEchange(models.Model):
    """Historique des échanges avec le prospect"""
    TYPE_ECHANGE_CHOICES = [
        ('appel', 'Appel téléphonique'),
        ('email', 'Email'),
        ('rdv', 'Rendez-vous'),
        ('message', 'Message WhatsApp'),
        ('autre', 'Autre'),
    ]
    
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, related_name='historiques')
    type_echange = models.CharField(max_length=20, choices=TYPE_ECHANGE_CHOICES)
    date_echange = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    contenu = models.TextField()
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_echange']
        verbose_name = "Historique d'échange"
        verbose_name_plural = "Historiques d'échanges"
    
    def __str__(self):
        return f"{self.get_type_echange_display()} - {self.date_echange.strftime('%d/%m/%Y %H:%M')}"