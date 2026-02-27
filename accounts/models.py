from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string


class User(AbstractUser):
    ROLE_CHOICES = (
        ('super_admin', 'Super Administrateur'),
        ('responsable', 'Responsable Pédagogique'),
        ('assistante', 'Assistante'),
        ('entreprise', 'Entreprise Partenaire'),
        ('formateur', 'Formateur'),
        ('etudiant', 'Étudiant'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='etudiant')
    phone = models.CharField(max_length=20, blank=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Mot de passe en clair — stocké uniquement pour affichage dans l'interface admin
    password_plain = models.CharField(max_length=255, blank=True, null=True, verbose_name="Mot de passe (affiché)")

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.'
    )

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

    class Meta:
        db_table = 'users'


class PasswordResetCode(models.Model):
    """Modèle pour stocker les codes de réinitialisation de mot de passe"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_codes')
    code = models.CharField(max_length=6)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        """Vérifie si le code est valide (moins de 5 minutes et non utilisé)"""
        expiry_time = self.created_at + timedelta(minutes=5)
        return not self.is_used and timezone.now() <= expiry_time

    @staticmethod
    def generate_code():
        """Génère un code aléatoire à 6 chiffres"""
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"Code pour {self.email} - {self.code}"

    class Meta:
        db_table = 'password_reset_codes'