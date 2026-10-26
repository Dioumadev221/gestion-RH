from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Contrat, Departement, Employe
from .serializers import DepartementSerializer, EmployeSerializer


class PaginationEmployes(PageNumberPagination):
    """?page=2 pour changer de page, ?page_size=10 pour changer la taille (100 maximum)."""

    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,          # nombre total d'employés (après filtres)
            'page': self.page.number,                    # page actuelle
            'nb_pages': self.page.paginator.num_pages,   # nombre de pages
            'page_size': self.get_page_size(self.request),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,                             # les employés de la page
        })


class EmployeViewSet(viewsets.ModelViewSet):
    """
    GET    /api/employes/                  liste paginée (?page=, ?page_size=, ?departement=<id>, ?search=<texte>)
    POST   /api/employes/                  ajout (avec ses contrats)
    GET    /api/employes/<id>/             fiche
    PUT    /api/employes/<id>/             modification
    PATCH  /api/employes/<id>/             modification partielle
    DELETE /api/employes/<id>/             suppression (avec ses contrats)
    """

    serializer_class = EmployeSerializer
    pagination_class = PaginationEmployes

    def get_queryset(self):
        employes = (
            Employe.objects.select_related('departement')
            .prefetch_related('contrats')
            .order_by('nom', 'prenom')
        )
        departement = self.request.query_params.get('departement')
        recherche = self.request.query_params.get('search', '').strip()
        if departement:
            employes = employes.filter(departement_id=departement)
        if recherche:
            employes = employes.filter(
                Q(nom__icontains=recherche)
                | Q(prenom__icontains=recherche)
                | Q(matricule__icontains=recherche)
                | Q(poste__icontains=recherche)
            )
        return employes

    @transaction.atomic
    def perform_destroy(self, employe):
        # Contrat.emploi est en PROTECT : on supprime explicitement les contrats d'abord
        employe.contrats.all().delete()
        employe.delete()


class DepartementViewSet(viewsets.ModelViewSet):
    serializer_class = DepartementSerializer

    def get_queryset(self):
        return Departement.objects.annotate(nb_employes=Count('emplois')).order_by('nom')


SEUIL_ECHEANCE_JOURS = 60


@api_view(['GET'])
def statistiques(request):
    """Chiffres clés affichés en haut de la liste des employés."""
    aujourd_hui = timezone.localdate()
    return Response({
        'employes': Employe.objects.count(),
        'departements': Departement.objects.count(),
        'cdi': Contrat.objects.filter(type_contrat='CDI').count(),
        'cdd': Contrat.objects.filter(type_contrat='CDD').count(),
        'prestataires': Contrat.objects.filter(type_contrat='PRESTATAIRE').count(),
        # Contrats qui se terminent dans les 60 prochains jours : à renouveler ou clôturer
        'echeances': Contrat.objects.filter(
            date_fin__gte=aujourd_hui, date_fin__lte=aujourd_hui + timedelta(days=SEUIL_ECHEANCE_JOURS)
        ).count(),
        'seuil_echeance': SEUIL_ECHEANCE_JOURS,
    })
