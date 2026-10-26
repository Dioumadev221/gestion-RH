from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Contrat, Departement, Employe
from .serializers import DepartementSerializer, EmployeSerializer


class EmployeViewSet(viewsets.ModelViewSet):
    """
    GET    /api/employes/                  liste (?departement=<id>, ?search=<texte>)
    POST   /api/employes/                  ajout (avec ses contrats)
    GET    /api/employes/<id>/             fiche
    PUT    /api/employes/<id>/             modification
    PATCH  /api/employes/<id>/             modification partielle
    DELETE /api/employes/<id>/             suppression
    """

    serializer_class = EmployeSerializer

    def get_queryset(self):
        employes = Employe.objects.select_related('departement').prefetch_related('contrats')
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


class DepartementViewSet(viewsets.ModelViewSet):
    serializer_class = DepartementSerializer

    def get_queryset(self):
        return Departement.objects.select_related('responsable').annotate(nb_employes=Count('employes'))


@api_view(['GET'])
def statistiques(request):
    """Chiffres clés affichés en haut de la liste des employés."""
    return Response({
        'employes': Employe.objects.count(),
        'departements': Departement.objects.count(),
        'cdi': Contrat.objects.filter(type=Contrat.Type.CDI).count(),
        'cdd': Contrat.objects.filter(type=Contrat.Type.CDD).count(),
        'prestataires': Contrat.objects.filter(type=Contrat.Type.PRESTATAIRE).count(),
    })
