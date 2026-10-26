from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('employes', views.EmployeViewSet, basename='employe')
router.register('departements', views.DepartementViewSet, basename='departement')

urlpatterns = [
    path('statistiques/', views.statistiques, name='statistiques'),
    path('', include(router.urls)),
]
