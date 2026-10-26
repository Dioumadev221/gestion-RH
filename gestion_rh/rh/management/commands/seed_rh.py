from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from rh.models import Contrat, Departement, Employe

AUJOURD_HUI = timezone.localdate()


def dans(jours):
    """Date relative à aujourd'hui : les échéances de démo restent réalistes quel que soit le jour."""
    return AUJOURD_HUI + timedelta(days=jours)


# nom, description, responsable
DEPARTEMENTS = [
    ('TIC', "Technologies de l'information et de la communication : développement, réseaux, informatique", 'Awa Diop'),
    ('Automobile', 'Mécanique et électricité automobile', 'Lamine Sarr'),
    ('Administration', 'Scolarité, secrétariat, comptabilité et direction', 'Fatou Sow'),
]

# matricule, prénom, nom, poste, département, date d'embauche, téléphone, contrat (type, début, fin)
EMPLOYES = [
    ('EMP-001', 'Awa', 'Diop', 'Enseignante Python', 'TIC', date(2019, 9, 1), 771234501,
     ('CDI', date(2019, 9, 1), None)),
    ('EMP-002', 'Moussa', 'Ba', 'Enseignant Réseaux', 'TIC', date(2022, 10, 1), 781234502,
     ('CDD', dans(-340), dans(25))),
    ('EMP-003', 'Fatou', 'Sow', 'Responsable scolarité', 'Administration', date(2018, 1, 15), 761234503,
     ('CDI', date(2018, 1, 15), None)),
    ('EMP-004', 'Ibrahima', 'Ndiaye', 'Secrétaire de direction', 'Administration', date(2023, 3, 1), 771234504,
     ('CDD', dans(-200), dans(165))),
    ('EMP-005', 'Aminata', 'Fall', 'Comptable', 'Administration', date(2020, 6, 1), 701234505,
     ('CDI', date(2020, 6, 1), None)),
    ('EMP-006', 'Cheikh', 'Gueye', 'Technicien informatique', 'TIC', date(2021, 2, 1), 771234506,
     ('CDI', date(2021, 2, 1), None)),
    ('EMP-007', 'Mariama', 'Sy', 'Formatrice Bootstrap', 'TIC', date(2025, 1, 6), 781234507,
     ('PRESTATAIRE', dans(-120), dans(48))),
    ('EMP-008', 'Ousmane', 'Faye', 'Formateur mécanique automobile', 'Automobile', date(2024, 4, 1), 761234508,
     ('CDD', dans(-400), dans(-12))),
    ('EMP-009', 'Lamine', 'Sarr', 'Formateur électricité automobile', 'Automobile', date(2017, 10, 2), 771234509,
     ('CDI', date(2017, 10, 2), None)),
]


class Command(BaseCommand):
    help = 'Crée des départements, employés et contrats de démonstration (sans doublons).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reinitialiser',
            action='store_true',
            help='Supprime TOUS les départements, employés et contrats avant de recharger la démo.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reinitialiser']:
            # Contrat.emploi est en PROTECT : les contrats doivent partir en premier
            Contrat.objects.all().delete()
            Employe.objects.all().delete()
            Departement.objects.all().delete()
            self.stdout.write('Données RH supprimées.')

        departements = {}
        for nom, description, responsable in DEPARTEMENTS:
            departements[nom], _ = Departement.objects.get_or_create(
                nom=nom, defaults={'description': description, 'responsable': responsable}
            )

        crees = 0
        for numero, (matricule, prenom, nom, poste, departement, embauche, telephone, contrat) in enumerate(EMPLOYES, 1):
            if Employe.objects.filter(matricule=matricule).exists():
                continue
            employe = Employe.objects.create(
                matricule=matricule,
                prenom=prenom,
                nom=nom,
                email=f'{prenom}.{nom}@isep-at.sn'.lower(),
                telephone=telephone,
                date_embauche=embauche,
                poste=poste,
                departement=departements[departement],
            )
            type_contrat, debut, fin = contrat
            Contrat.objects.get_or_create(
                reference=f'CTR-{debut.year}-{numero:03d}',
                defaults={'emploi': employe, 'type_contrat': type_contrat, 'date_debut': debut, 'date_fin': fin},
            )
            crees += 1

        self.stdout.write(self.style.SUCCESS(
            f'{len(departements)} départements, {crees} employé(s) créé(s) ({Employe.objects.count()} au total).'
        ))
