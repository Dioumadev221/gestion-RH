from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Contrat, Departement, Employe


class ContratSerializer(serializers.ModelSerializer):
    # id modifiable : il permet de savoir quel contrat existant on met à jour
    id = serializers.IntegerField(required=False)
    # L'unicité de la référence est vérifiée par EmployeSerializer (qui connaît les contrats modifiés)
    reference = serializers.CharField(max_length=50)
    type_contrat_display = serializers.CharField(source='get_type_contrat_display', read_only=True)

    class Meta:
        model = Contrat
        fields = ['id', 'reference', 'type_contrat', 'type_contrat_display', 'date_debut', 'date_fin']

    def validate(self, attrs):
        type_contrat = attrs.get('type_contrat')
        debut, fin = attrs.get('date_debut'), attrs.get('date_fin')
        if type_contrat in ('CDD', 'PRESTATAIRE') and not fin:
            raise serializers.ValidationError(
                {'date_fin': 'La date de fin est obligatoire pour un CDD ou une prestation.'}
            )
        if debut and fin and fin < debut:
            raise serializers.ValidationError({'date_fin': 'La date de fin doit être après la date de début.'})
        return attrs


def contrat_actuel(employe):
    """Contrat en cours aujourd'hui, ou le plus récent à défaut."""
    aujourd_hui = timezone.localdate()
    contrats = sorted(employe.contrats.all(), key=lambda c: c.date_debut, reverse=True)
    for contrat in contrats:
        if contrat.date_debut <= aujourd_hui and (contrat.date_fin is None or contrat.date_fin >= aujourd_hui):
            return contrat
    return contrats[0] if contrats else None


class EmployeSerializer(serializers.ModelSerializer):
    """Employé avec ses contrats imbriqués (le contrat est un sous-modèle de l'employé)."""

    matricule = serializers.CharField(
        max_length=100,
        validators=[UniqueValidator(Employe.objects.all(), message='Ce matricule est déjà attribué à un employé.')],
    )
    contrats = ContratSerializer(many=True, required=False)
    departement_nom = serializers.CharField(source='departement.nom', read_only=True)
    contrat_actuel = serializers.SerializerMethodField()

    class Meta:
        model = Employe
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'email', 'telephone', 'date_embauche',
            'poste', 'departement', 'departement_nom', 'contrat_actuel', 'contrats',
        ]

    def get_contrat_actuel(self, employe):
        contrat = contrat_actuel(employe)
        return ContratSerializer(contrat).data if contrat else None

    def validate_contrats(self, contrats):
        references = [c['reference'] for c in contrats]
        if len(references) != len(set(references)):
            raise serializers.ValidationError('Deux contrats ne peuvent pas avoir la même référence.')

        # Une référence ne doit pas déjà appartenir à un autre contrat que ceux qu'on modifie
        ids_modifies = {c['id'] for c in contrats if c.get('id')}
        erreurs, conflit = [], False
        for contrat in contrats:
            pris = Contrat.objects.filter(reference=contrat['reference']).exclude(id__in=ids_modifies).exists()
            erreurs.append({'reference': ['Cette référence de contrat existe déjà.']} if pris else {})
            conflit = conflit or pris
        if conflit:
            raise serializers.ValidationError(erreurs)
        return contrats

    @transaction.atomic
    def create(self, validated_data):
        contrats = validated_data.pop('contrats', [])
        employe = Employe.objects.create(**validated_data)
        for data in contrats:
            data.pop('id', None)
            Contrat.objects.create(emploi=employe, **data)
        return employe

    @transaction.atomic
    def update(self, employe, validated_data):
        contrats = validated_data.pop('contrats', None)
        employe = super().update(employe, validated_data)

        # Liste de contrats envoyée : on supprime ceux qui ont disparu, puis on met à jour / ajoute
        if contrats is not None:
            existants = {c.id: c for c in employe.contrats.all()}
            conserves = {c.get('id') for c in contrats if c.get('id') in existants}
            employe.contrats.filter(id__in=set(existants) - conserves).delete()
            for data in contrats:
                contrat_id = data.pop('id', None)
                if contrat_id in existants:
                    contrat = existants[contrat_id]
                    for champ, valeur in data.items():
                        setattr(contrat, champ, valeur)
                    contrat.save()
                else:
                    Contrat.objects.create(emploi=employe, **data)
        return employe


class DepartementSerializer(serializers.ModelSerializer):
    nb_employes = serializers.SerializerMethodField()

    class Meta:
        model = Departement
        fields = ['id', 'nom', 'description', 'responsable', 'nb_employes']

    def get_nb_employes(self, departement):
        nb = getattr(departement, 'nb_employes', None)
        return nb if nb is not None else departement.emplois.count()
