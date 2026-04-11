# marketing_mail/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Liste de tous les emails (avec filtres)
    path('', views.liste_emails, name='marketing-mail-liste'),
    
    # Créer + envoyer un email
    path('envoyer/', views.creer_envoyer_email, name='marketing-mail-envoyer'),
    
    # Détail d'un email
    path('<int:pk>/', views.detail_email, name='marketing-mail-detail'),
    
    # Archiver plusieurs emails
    path('archiver/', views.archiver_emails, name='marketing-mail-archiver'),
    
    # Estimer le nombre de destinataires
    path('estimer/', views.estimer_destinataires, name='marketing-mail-estimer'),
    
    # Liste des formations (pour les chips)
    path('formations/', views.liste_formations_marketing, name='marketing-mail-formations'),
    
    # Liste des formations par type de groupe
    path('formations/<str:type_groupe>/', views.liste_formations_par_type, name='marketing-mail-formations-par-type'),
    
    # Debug
    path('debug/', views.debug_emails, name='marketing-mail-debug'),
]