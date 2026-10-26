from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from rh.models import Contrat, Departement, Employe

DEPARTEMENTS = [
    ('Pédagogie', 'Enseignants et coordination des formations'),
    ('Administration', 'Scolarité, secrétariat et direction'),
    ('Finances', 'Comptabilité, paie et budget'),
    ('Services techniques', 'Informatique, maintenance et logistique'),
]

# matricule, prénom, nom, poste, département, date d'embauche, contrat (type, début, fin, salaire)
EMPLOYES = [
    ('EMP-001', 'Awa', 'Diop', 'Enseignante Python', 'Pédagogie', date(2019, 9, 1),
     ('CDI', date(2019, 9, 1), None, 850000)),
    ('EMP-002', 'Moussa', 'Ba', 'Enseignant Réseaux', 'Pédagogie', date(2022, 10, 1),
     ('CDD', date(2024, 10, 1), date(2026, 9, 30), 650000)),
    ('EMP-003', 'Fatou', 'Sow', 'Responsable scolarité', 'Administration', date(2018, 1, 15),
     ('CDI', date(2018, 1, 15), None, 700000)),
    ('EMP-004', 'Ibrahima', 'Ndiaye', 'Secrétaire de direction', 'Administration', date(2023, 3, 1),
     ('CDD', date(2023, 3, 1), date(2026, 2, 28), 400000)),
    ('EMP-005', 'Aminata', 'Fall', 'Comptable', 'Finances', date(2020, 6, 1),
     ('CDI', date(2020, 6, 1), None, 750000)),
    ('EMP-006', 'Cheikh', 'Gueye', 'Technicien informatique', 'Services techniques', date(2021, 2, 1),
     ('CDI', date(2021, 2, 1), None, 550000)),
    ('EMP-007', 'Mariama', 'Sy', 'Formatrice Bootstrap', 'Pédagogie', date(2025, 1, 6),
     ('PRESTATAIRE', date(2025, 1, 6), date(2026, 7, 31), 500000)),
    ('EMP-008', 'Ousmane', 'Faye', 'Agent de maintenance', 'Services techniques', date(2024, 4, 1),
     ('CDD', date(2024, 4, 1), date(2026, 3, 31), 250000)),
]

RESPONSABLES = {
    'Pédagogie': 'EMP-001',
    'Administration': 'EMP-003',
    'Finances': 'EMP-005',
    'Services techniques': 'EMP-006',
}


class Command(BaseCommand):
    help = 'Crée des départements, employés et contrats de démonstration (sans doublons).'

    @transaction.atomic
    def handle(self, *args, **options):
        departements = {}
        for nom, description in DEPARTEMENTS:
            departements[nom], _ = Departement.objects.get_or_create(nom=nom, defaults={'description': description})

        crees = 0
        for matricule, prenom, nom, poste, departement, embauche, (type_c, debut, fin, salaire) in EMPLOYES:
            employe, cree = Employe.objects.get_or_create(
                matricule=matricule,
                defaults={
                    'prenom': prenom,
                    'nom': nom,
                    'email': f'{prenom}.{nom}@isep-at.sn'.lower(),
                    'telephone': f'77 000 00 {matricule[-2:]}',
                    'date_embauche': embauche,
                    'poste': poste,
                    'departement': departements[departement],
                },
            )
            if cree:
                crees += 1
                Contrat.objects.create(employe=employe, type=type_c, date_debut=debut, date_fin=fin, salaire=salaire)

        for departement, matricule in RESPONSABLES.items():
            dep = departements[departement]
            if dep.responsable_id is None:
                dep.responsable = Employe.objects.get(matricule=matricule)
                dep.save()

        self.stdout.write(self.style.SUCCESS(
            f'{len(departements)} départements, {crees} employé(s) créé(s) ({Employe.objects.count()} au total).'
        ))
