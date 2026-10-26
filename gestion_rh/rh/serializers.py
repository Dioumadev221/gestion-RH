from django.db import transaction
from rest_framework import serializers

from .models import Contrat, Departement, Employe


class ContratSerializer(serializers.ModelSerializer):
    # id modifiable : il permet de savoir quel contrat existant on met à jour
    id = serializers.IntegerField(required=False)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Contrat
        fields = ['id', 'type', 'type_display', 'date_debut', 'date_fin', 'salaire']

    def validate(self, attrs):
        type_contrat = attrs.get('type')
        debut, fin = attrs.get('date_debut'), attrs.get('date_fin')
        if type_contrat in (Contrat.Type.CDD, Contrat.Type.PRESTATAIRE) and not fin:
            raise serializers.ValidationError(
                {'date_fin': 'La date de fin est obligatoire pour un CDD ou un prestataire.'}
            )
        if debut and fin and fin < debut:
            raise serializers.ValidationError({'date_fin': 'La date de fin doit être après la date de début.'})
        return attrs


class EmployeSerializer(serializers.ModelSerializer):
    """Employé avec ses contrats imbriqués (le contrat est un sous-modèle de l'employé)."""

    contrats = ContratSerializer(many=True, required=False)
    departement_nom = serializers.CharField(source='departement.nom', read_only=True, default=None)
    contrat_actuel = serializers.SerializerMethodField()

    class Meta:
        model = Employe
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'email', 'telephone', 'date_embauche',
            'poste', 'departement', 'departement_nom', 'contrat_actuel', 'contrats',
        ]

    def get_contrat_actuel(self, employe):
        contrat = employe.contrat_actuel
        return ContratSerializer(contrat).data if contrat else None

    @transaction.atomic
    def create(self, validated_data):
        contrats = validated_data.pop('contrats', [])
        employe = Employe.objects.create(**validated_data)
        for data in contrats:
            data.pop('id', None)
            Contrat.objects.create(employe=employe, **data)
        return employe

    @transaction.atomic
    def update(self, employe, validated_data):
        contrats = validated_data.pop('contrats', None)
        employe = super().update(employe, validated_data)

        # Liste de contrats envoyée : on met à jour, on ajoute, et on supprime ceux qui ont disparu
        if contrats is not None:
            existants = {c.id: c for c in employe.contrats.all()}
            conserves = set()
            for data in contrats:
                contrat_id = data.pop('id', None)
                if contrat_id in existants:
                    contrat = existants[contrat_id]
                    for champ, valeur in data.items():
                        setattr(contrat, champ, valeur)
                    contrat.save()
                    conserves.add(contrat_id)
                else:
                    Contrat.objects.create(employe=employe, **data)
            employe.contrats.filter(id__in=set(existants) - conserves).delete()
        return employe


class DepartementSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source='responsable.nom_complet', read_only=True, default=None)
    nb_employes = serializers.SerializerMethodField()

    class Meta:
        model = Departement
        fields = ['id', 'nom', 'description', 'responsable', 'responsable_nom', 'nb_employes']

    def get_nb_employes(self, departement):
        nb = getattr(departement, 'nb_employes', None)
        return nb if nb is not None else departement.employes.count()
