# diplomes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # NOTE: 'certifier/' doit être déclaré AVANT '<int:pk>/'
    # pour éviter que Django ne tente de caster "certifier" en entier.
    path('certifier/',  views.certifier_etudiant, name='certifier-etudiant'),
    path('',            views.diplome_list,        name='diplome-list'),
    path('<int:pk>/',   views.diplome_detail,      name='diplome-detail'),
]

# À ajouter dans votre urls.py principal :
# path('api/diplomes/', include('diplomes.urls')),