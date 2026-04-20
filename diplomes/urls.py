# diplomes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ── Relances — routes fixes en PREMIER (avant <int:pk>/) ──────────
    path('relances/all/',          views.all_diplome_relances,         name='diplome-relances-all'),
    path('relances/count-today/',  views.diplome_relances_count_today, name='diplome-relances-count-today'),
    path('relances/<int:pk>/',     views.diplome_relance_detail,       name='diplome-relance-detail'),
    path('relances/<int:pk>/ok/',  views.diplome_relance_action_ok,    name='diplome-relance-ok'),

    # ── Certifier (avant <int:pk>/ pour éviter le cast "certifier") ───
    path('certifier/',             views.certifier_etudiant,           name='certifier-etudiant'),

    # ── Diplômes ───────────────────────────────────────────────────────
    path('',                       views.diplome_list,                 name='diplome-list'),
    path('<int:pk>/',              views.diplome_detail,               name='diplome-detail'),
    path('<int:pk>/envoyer-attestation/', views.envoyer_attestation,  name='envoyer-attestation'),
    path('<int:diplome_pk>/relances/',    views.diplome_relance_list_create, name='diplome-relances'),
]

