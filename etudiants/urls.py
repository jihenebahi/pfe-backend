# etudiants/urls.py
from django.urls import path
from . import views

# etudiants/urls.py
urlpatterns = [
    path('', views.etudiant_list_create, name='etudiant-list-create'),
    path('<int:pk>/', views.etudiant_detail, name='etudiant-detail'),
    path('<int:pk>/formations/<int:formation_pk>/attester/', views.attester_formation, name='attester-formation'),
    
    # ✅ AJOUTER CETTE LIGNE (doit être AVANT les URLs avec paramètres)
    path('relances/all/', views.all_etudiant_relances, name='all-etudiant-relances'),
    
    # Relances étudiants
    path('relances/count-today/', views.etudiant_relances_count_today, name='etudiant-relances-count'),
    path('relances/<int:pk>/', views.etudiant_relance_detail, name='etudiant-relance-detail'),
    path('relances/<int:pk>/ok/', views.etudiant_relance_action_ok, name='etudiant-relance-ok'),
    path('<int:etudiant_pk>/relances/', views.etudiant_relance_list_create, name='etudiant-relances'),
]