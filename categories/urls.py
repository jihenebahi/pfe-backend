from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_categories, name='liste_categories'),
    path('ajouter/', views.ajouter_categorie, name='ajouter_categorie'),
]