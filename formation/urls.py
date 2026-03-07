from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_formations, name='liste_formations'),
    path('ajouter/', views.ajouter_formation, name='ajouter_formation'),
    path('<int:pk>/', views.detail_formation, name='detail_formation'),
    path('modifier/<int:pk>/', views.modifier_formation, name='modifier_formation'),
    path('supprimer/<int:pk>/', views.supprimer_formation, name='supprimer_formation'),
    path('categories-disponibles/', views.liste_categories_pour_formations, name='categories_pour_formations'),
    # ✅ NOUVEAU
    path('formateurs-disponibles/', views.liste_formateurs_pour_formations, name='formateurs_pour_formations'),
]