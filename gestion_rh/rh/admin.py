from django.contrib import admin

from .models import Contrat, Departement, Employe


class ContratInline(admin.TabularInline):
    """Les contrats se gèrent directement depuis la fiche de l'employé."""

    model = Contrat
    extra = 1


@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'nom', 'prenom', 'poste', 'departement', 'date_embauche']
    list_filter = ['departement', 'contrats__type_contrat']
    search_fields = ['matricule', 'nom', 'prenom', 'email', 'poste']
    inlines = [ContratInline]

    def delete_model(self, request, obj):
        # Contrat.emploi est en PROTECT : suppression des contrats avant l'employé
        obj.contrats.all().delete()
        obj.delete()

    def delete_queryset(self, request, queryset):
        Contrat.objects.filter(emploi__in=queryset).delete()
        queryset.delete()


class EmployeInline(admin.TabularInline):
    model = Employe
    extra = 0
    fields = ['matricule', 'nom', 'prenom', 'poste']
    show_change_link = True


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ['nom', 'responsable']
    search_fields = ['nom', 'responsable']
    inlines = [EmployeInline]


@admin.register(Contrat)
class ContratAdmin(admin.ModelAdmin):
    list_display = ['reference', 'emploi', 'type_contrat', 'date_debut', 'date_fin']
    list_filter = ['type_contrat']
    search_fields = ['reference', 'emploi__nom', 'emploi__prenom', 'emploi__matricule']
