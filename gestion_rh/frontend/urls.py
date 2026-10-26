from django.urls import path

from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.liste_employes, name='liste_employes'),
    path('employes/ajouter/', views.ajouter_employe, name='ajouter_employe'),
    path('employes/<int:pk>/', views.detail_employe, name='detail_employe'),
    path('employes/<int:pk>/modifier/', views.modifier_employe, name='modifier_employe'),
    path('departements/', views.liste_departements, name='liste_departements'),
]
