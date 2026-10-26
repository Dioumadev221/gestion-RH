from datetime import date

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import Contrat, Departement, Employe


class ApiRHTests(APITestCase):
    def setUp(self):
        self.rh = User.objects.create_user('rh', password='Rh-test-123', is_staff=True)
        self.client.force_login(self.rh)
        self.pedagogie = Departement.objects.create(nom='Pédagogie')
        self.finances = Departement.objects.create(nom='Finances')
        self.awa = Employe.objects.create(
            matricule='EMP-001', nom='Diop', prenom='Awa', email='awa@isep-at.sn',
            telephone='77 123 45 67', date_embauche=date(2020, 1, 1), poste='Enseignante',
            departement=self.pedagogie,
        )
        Contrat.objects.create(employe=self.awa, type='CDI', date_debut=date(2020, 1, 1), salaire=800000)
        Employe.objects.create(
            matricule='EMP-002', nom='Fall', prenom='Aminata', email='aminata@isep-at.sn',
            telephone='77 222 22 22', date_embauche=date(2021, 1, 1), poste='Comptable',
            departement=self.finances,
        )

    def donnees_employe(self, **extra):
        donnees = {
            'matricule': 'EMP-010', 'nom': 'Ndiaye', 'prenom': 'Ibrahima',
            'email': 'ibrahima@isep-at.sn', 'telephone': '77 999 99 99',
            'date_embauche': '2025-01-06', 'poste': 'Secrétaire', 'departement': self.finances.id,
            'contrats': [{'type': 'CDD', 'date_debut': '2025-01-06', 'date_fin': '2026-01-05', 'salaire': '400000'}],
        }
        donnees.update(extra)
        return donnees

    # Accès
    def test_api_reservee_au_staff(self):
        self.client.logout()
        self.assertEqual(self.client.get('/api/employes/').status_code, 403)
        simple = User.objects.create_user('simple', password='Simple-test-123')
        self.client.force_login(simple)
        self.assertEqual(self.client.get('/api/employes/').status_code, 403)

    # a) Liste des employés + filtre par département
    def test_liste_employes(self):
        rep = self.client.get('/api/employes/')
        self.assertEqual(rep.status_code, 200)
        self.assertEqual([e['nom'] for e in rep.data], ['Diop', 'Fall'])
        self.assertEqual(rep.data[0]['departement_nom'], 'Pédagogie')
        self.assertEqual(rep.data[0]['contrat_actuel']['type'], 'CDI')

    def test_filtre_par_departement(self):
        rep = self.client.get('/api/employes/', {'departement': self.finances.id})
        self.assertEqual([e['nom'] for e in rep.data], ['Fall'])

    def test_recherche(self):
        rep = self.client.get('/api/employes/', {'search': 'awa'})
        self.assertEqual([e['matricule'] for e in rep.data], ['EMP-001'])

    # b) Ajout avec son contrat
    def test_ajout_employe_avec_contrat(self):
        rep = self.client.post('/api/employes/', self.donnees_employe(), format='json')
        self.assertEqual(rep.status_code, 201, rep.data)
        employe = Employe.objects.get(matricule='EMP-010')
        self.assertEqual(employe.contrats.get().type, 'CDD')

    def test_validation_des_donnees(self):
        rep = self.client.post('/api/employes/', self.donnees_employe(
            matricule='EMP-001', email='pas-un-email',
            contrats=[{'type': 'CDD', 'date_debut': '2025-01-06', 'salaire': '400000'}],
        ), format='json')
        self.assertEqual(rep.status_code, 400)
        self.assertIn('matricule', rep.data)
        self.assertIn('email', rep.data)
        self.assertIn('date_fin', rep.data['contrats'][0])
        self.assertFalse(Employe.objects.filter(nom='Ndiaye').exists())

    def test_date_fin_avant_date_debut(self):
        rep = self.client.post('/api/employes/', self.donnees_employe(
            contrats=[{'type': 'CDD', 'date_debut': '2025-01-06', 'date_fin': '2024-01-01', 'salaire': '1'}],
        ), format='json')
        self.assertEqual(rep.status_code, 400)

    # c) Modification
    def test_modification_employe_et_contrats(self):
        contrat = self.awa.contrats.get()
        rep = self.client.put(f'/api/employes/{self.awa.id}/', self.donnees_employe(
            matricule='EMP-001', nom='Diop', prenom='Awa', email='awa@isep-at.sn', poste='Directrice des études',
            contrats=[
                {'id': contrat.id, 'type': 'CDI', 'date_debut': '2020-01-01', 'salaire': '950000'},
                {'type': 'PRESTATAIRE', 'date_debut': '2026-01-01', 'date_fin': '2026-06-30', 'salaire': '100000'},
            ],
        ), format='json')
        self.assertEqual(rep.status_code, 200, rep.data)
        self.awa.refresh_from_db()
        self.assertEqual(self.awa.poste, 'Directrice des études')
        contrat.refresh_from_db()
        self.assertEqual(contrat.salaire, 950000)
        self.assertEqual(self.awa.contrats.count(), 2)

    def test_modification_supprime_les_contrats_retires(self):
        rep = self.client.patch(f'/api/employes/{self.awa.id}/', {'contrats': []}, format='json')
        self.assertEqual(rep.status_code, 200)
        self.assertFalse(self.awa.contrats.exists())

    # d) Suppression
    def test_suppression_employe(self):
        rep = self.client.delete(f'/api/employes/{self.awa.id}/')
        self.assertEqual(rep.status_code, 204)
        self.assertFalse(Employe.objects.filter(pk=self.awa.id).exists())
        self.assertFalse(Contrat.objects.exists())

    # Départements et statistiques
    def test_departements_et_statistiques(self):
        self.pedagogie.responsable = self.awa
        self.pedagogie.save()
        rep = self.client.get('/api/departements/')
        pedagogie = next(d for d in rep.data if d['nom'] == 'Pédagogie')
        self.assertEqual(pedagogie['nb_employes'], 1)
        self.assertEqual(pedagogie['responsable_nom'], 'Awa Diop')

        stats = self.client.get('/api/statistiques/').data
        self.assertEqual(stats['employes'], 2)
        self.assertEqual(stats['cdi'], 1)


class PagesTests(APITestCase):
    def test_pages_protegees(self):
        rep = self.client.get('/')
        self.assertEqual(rep.status_code, 302)
        self.assertIn('/admin/login/', rep['Location'])

    def test_pages_accessibles_au_staff(self):
        staff = User.objects.create_user('rh', password='Rh-test-123', is_staff=True)
        self.client.force_login(staff)
        employe = Employe.objects.create(
            matricule='EMP-001', nom='Diop', prenom='Awa', email='awa@isep-at.sn',
            telephone='77 123 45 67', date_embauche=date(2020, 1, 1), poste='Enseignante',
        )
        for url in ['/', '/employes/ajouter/', f'/employes/{employe.id}/',
                    f'/employes/{employe.id}/modifier/', '/departements/']:
            rep = self.client.get(url)
            self.assertEqual(rep.status_code, 200, url)
            self.assertContains(rep, 'bootstrap@5.3.3')
