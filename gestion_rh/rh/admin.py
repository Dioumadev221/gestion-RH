from django.contrib import admin

from .models import Contrat, Departement, Employe


class ContratInline(admin.TabularInline):
    """Les contrats se gèrent directement depuis la fiche de l'employé."""

    model = Contrat
    extra = 1


@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'nom', 'prenom', 'poste', 'departement', 'date_embauche']
    list_filter = ['departement', 'contrats__type']
    search_fields = ['matricule', 'nom', 'prenom', 'email', 'poste']
    inlines = [ContratInline]


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ['nom', 'responsable']
    search_fields = ['nom']


@admin.register(Contrat)
class ContratAdmin(admin.ModelAdmin):
    list_display = ['employe', 'type', 'date_debut', 'date_fin', 'salaire']
    list_filter = ['type']
    search_fields = ['employe__nom', 'employe__prenom', 'employe__matricule']
