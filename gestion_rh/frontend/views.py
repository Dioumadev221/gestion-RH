from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

# Ces vues ne font qu'afficher les pages : les données sont chargées
# en JavaScript depuis l'API (/api/...), voir static/frontend/app.js.


@staff_member_required
def liste_employes(request):
    return render(request, 'frontend/liste_employes.html')


@staff_member_required
def detail_employe(request, pk):
    return render(request, 'frontend/detail_employe.html', {'employe_id': pk})


@staff_member_required
def ajouter_employe(request):
    return render(request, 'frontend/form_employe.html', {'employe_id': None})


@staff_member_required
def modifier_employe(request, pk):
    return render(request, 'frontend/form_employe.html', {'employe_id': pk})


@staff_member_required
def liste_departements(request):
    return render(request, 'frontend/departements.html')
