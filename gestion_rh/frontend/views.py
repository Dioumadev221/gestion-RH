from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

from .forms import ConnexionRHForm

# Ces vues ne font qu'afficher les pages : les données sont chargées
# en JavaScript depuis l'API (/api/...), voir static/frontend/app.js.

reserve_rh = user_passes_test(lambda user: user.is_active and user.is_staff)


class ConnexionView(auth_views.LoginView):
    template_name = 'frontend/connexion.html'
    authentication_form = ConnexionRHForm
    redirect_authenticated_user = True


@reserve_rh
def liste_employes(request):
    return render(request, 'frontend/liste_employes.html')


@reserve_rh
def detail_employe(request, pk):
    return render(request, 'frontend/detail_employe.html', {'employe_id': pk})


@reserve_rh
def ajouter_employe(request):
    return render(request, 'frontend/form_employe.html', {'employe_id': None})


@reserve_rh
def modifier_employe(request, pk):
    return render(request, 'frontend/form_employe.html', {'employe_id': pk})


@reserve_rh
def liste_departements(request):
    return render(request, 'frontend/departements.html')
