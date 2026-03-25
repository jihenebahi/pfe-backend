# etudiants/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('',          views.etudiant_list_create, name='etudiant-list-create'),
    path('<int:pk>/', views.etudiant_detail,       name='etudiant-detail'),
]