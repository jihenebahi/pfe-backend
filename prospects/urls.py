# prospects/urls.py  ← version complète avec les routes Relance
from django.urls import path
from . import views

urlpatterns = [

    # ── Prospects CRUD ────────────────────────────────────────────────────
    path('',          views.prospect_list_create, name='prospect-list-create'),
    path('<int:pk>/', views.prospect_detail,       name='prospect-detail'),

    # ── Historiques d'échanges ────────────────────────────────────────────
    path('<int:prospect_pk>/historiques/',
         views.historique_list_create, name='historique-list-create'),

    # ── Statistiques ──────────────────────────────────────────────────────
    path('stats/', views.prospect_stats, name='prospect-stats'),

    # ── Conversion → Étudiant ─────────────────────────────────────────────
    path('<int:pk>/convert/', views.convert_to_etudiant, name='convert-to-etudiant'),

    # ── Import Excel ──────────────────────────────────────────────────────
    path('import/', views.import_prospects_excel, name='import-prospects'),

    # ── Relances ──────────────────────────────────────────────────────────

    # Toutes les relances (dashboard Home)
    path('relances/',                    views.all_relances,         name='all-relances'),

    # Compteur du jour (navbar badge)
    path('relances/count-today/',        views.relances_count_today, name='relances-count-today'),

    # Relances d'un prospect spécifique
    path('<int:prospect_pk>/relances/',  views.relance_list_create,  name='relance-list-create'),

    # Détail / modif / suppression d'une relance
    path('relances/<int:pk>/',           views.relance_detail,        name='relance-detail'),

    # Action "OK" — appel effectué
    path('relances/<int:pk>/ok/',        views.relance_action_ok,     name='relance-action-ok'),
]