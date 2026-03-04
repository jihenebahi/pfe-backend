from django.urls import path
from . import views

urlpatterns = [
    path('', views.FormateurListCreateView.as_view(), name='formateur-list-create'),
    path('<int:pk>/', views.FormateurDetailView.as_view(), name='formateur-detail'),
]