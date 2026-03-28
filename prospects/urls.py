# prospects/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ── Prospects CRUD ──
    path('',             views.prospect_list_create, name='prospect-list-create'),
    path('<int:pk>/',    views.prospect_detail,       name='prospect-detail'),

    # ── Historiques d'échanges ──
    path('<int:prospect_pk>/historiques/', views.historique_list_create, name='historique-list-create'),

    # ── Statistiques ──
    path('stats/', views.prospect_stats, name='prospect-stats'),
    
    path('<int:pk>/convert/', views.convert_to_etudiant, name='convert-to-etudiant'),

    # Import excel    
    path('import/',             views.import_prospects_excel,   name='import-prospects'),

]