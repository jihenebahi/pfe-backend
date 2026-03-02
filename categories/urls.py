from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.liste_categories,    name='liste_categories'),
    path('ajouter/',            views.ajouter_categorie,   name='ajouter_categorie'),
    path('<int:pk>/modifier/',  views.modifier_categorie,  name='modifier_categorie'),
    path('<int:pk>/supprimer/', views.supprimer_categorie, name='supprimer_categorie'),
]