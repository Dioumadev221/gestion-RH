from datetime import date, timedelta

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from .models import Contrat, Departement, Employe


class ApiRHTests(APITestCase):
    def setUp(self):
        self.rh = User.objects.create_user('rh', password='Rh-test-123', is_staff=True)
        self.client.force_login(self.rh)
        self.pedagogie = Departement.objects.create(nom='Pédagogie', responsable='Awa Diop')
        self.finances = Departement.objects.create(nom='Finances', responsable='Aminata Fall')
        self.awa = Employe.objects.create(
            matricule='EMP-001', nom='Diop', prenom='Awa', email='awa@isep-at.sn',
            telephone=771234567, date_embauche=date(2020, 1, 1), poste='Enseignante',
            departement=self.pedagogie,
        )
        Contrat.objects.create(emploi=self.awa, reference='CTR-001', type_contrat='CDI', date_debut=date(2020, 1, 1))
        Employe.objects.create(
            matricule='EMP-002', nom='Fall', prenom='Aminata', email='aminata@isep-at.sn',
            telephone=772222222, date_embauche=date(2021, 1, 1), poste='Comptable',
            departement=self.finances,
        )

    def donnees_employe(self, **extra):
        donnees = {
            'matricule': 'EMP-010', 'nom': 'Ndiaye', 'prenom': 'Ibrahima',
            'email': 'ibrahima@isep-at.sn', 'telephone': 779999999,
            'date_embauche': '2025-01-06', 'poste': 'Secrétaire', 'departement': self.finances.id,
            'contrats': [{'reference': 'CTR-010', 'type_contrat': 'CDD',
                          'date_debut': '2025-01-06', 'date_fin': '2026-01-05'}],
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
        self.assertEqual(rep.data[0]['contrat_actuel']['type_contrat'], 'CDI')

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
        self.assertEqual(employe.contrats.get().reference, 'CTR-010')

    def test_validation_des_donnees(self):
        rep = self.client.post('/api/employes/', self.donnees_employe(
            matricule='EMP-001', email='pas-un-email', departement=None,
            contrats=[{'reference': 'CTR-001', 'type_contrat': 'CDD', 'date_debut': '2025-01-06'}],
        ), format='json')
        self.assertEqual(rep.status_code, 400)
        self.assertIn('matricule', rep.data)
        self.assertIn('email', rep.data)
        self.assertIn('departement', rep.data)
        self.assertIn('date_fin', rep.data['contrats'][0])
        self.assertFalse(Employe.objects.filter(nom='Ndiaye').exists())

    def test_reference_de_contrat_deja_prise(self):
        rep = self.client.post('/api/employes/', self.donnees_employe(
            contrats=[{'reference': 'CTR-001', 'type_contrat': 'CDI', 'date_debut': '2025-01-06'}],
        ), format='json')
        self.assertEqual(rep.status_code, 400)
        self.assertIn('reference', rep.data['contrats'][0])

    def test_date_fin_avant_date_debut(self):
        rep = self.client.post('/api/employes/', self.donnees_employe(
            contrats=[{'reference': 'CTR-X', 'type_contrat': 'CDD', 'date_debut': '2025-01-06', 'date_fin': '2024-01-01'}],
        ), format='json')
        self.assertEqual(rep.status_code, 400)

    # c) Modification
    def test_modification_employe_et_contrats(self):
        contrat = self.awa.contrats.get()
        rep = self.client.put(f'/api/employes/{self.awa.id}/', self.donnees_employe(
            matricule='EMP-001', nom='Diop', prenom='Awa', email='awa@isep-at.sn', poste='Directrice des études',
            contrats=[
                {'id': contrat.id, 'reference': 'CTR-001', 'type_contrat': 'CDI', 'date_debut': '2019-09-01'},
                {'reference': 'CTR-011', 'type_contrat': 'PRESTATAIRE', 'date_debut': '2026-01-01', 'date_fin': '2026-06-30'},
            ],
        ), format='json')
        self.assertEqual(rep.status_code, 200, rep.data)
        self.awa.refresh_from_db()
        self.assertEqual(self.awa.poste, 'Directrice des études')
        contrat.refresh_from_db()
        self.assertEqual(contrat.date_debut, date(2019, 9, 1))
        self.assertEqual(self.awa.contrats.count(), 2)

    def test_modification_supprime_les_contrats_retires(self):
        rep = self.client.patch(f'/api/employes/{self.awa.id}/', {'contrats': []}, format='json')
        self.assertEqual(rep.status_code, 200)
        self.assertFalse(self.awa.contrats.exists())

    # d) Suppression (Contrat.emploi est en PROTECT)
    def test_suppression_employe_avec_contrats(self):
        rep = self.client.delete(f'/api/employes/{self.awa.id}/')
        self.assertEqual(rep.status_code, 204)
        self.assertFalse(Employe.objects.filter(pk=self.awa.id).exists())
        self.assertFalse(Contrat.objects.exists())

    # Départements et statistiques
    def test_departements_et_statistiques(self):
        rep = self.client.get('/api/departements/')
        pedagogie = next(d for d in rep.data if d['nom'] == 'Pédagogie')
        self.assertEqual(pedagogie['nb_employes'], 1)
        self.assertEqual(pedagogie['responsable'], 'Awa Diop')

        stats = self.client.get('/api/statistiques/').data
        self.assertEqual(stats['employes'], 2)
        self.assertEqual(stats['cdi'], 1)
        self.assertEqual(stats['echeances'], 0)

    def test_statistique_echeances(self):
        aujourd_hui = date.today()
        Contrat.objects.create(emploi=self.awa, reference='CTR-A', type_contrat='CDD', date_debut=aujourd_hui,
                               date_fin=aujourd_hui + timedelta(days=20))
        Contrat.objects.create(emploi=self.awa, reference='CTR-B', type_contrat='CDD', date_debut=aujourd_hui,
                               date_fin=aujourd_hui + timedelta(days=200))
        self.assertEqual(self.client.get('/api/statistiques/').data['echeances'], 1)


class PagesTests(APITestCase):
    def test_pages_protegees(self):
        rep = self.client.get('/')
        self.assertEqual(rep.status_code, 302)
        self.assertIn('/connexion/', rep['Location'])

    def test_connexion_reservee_au_staff(self):
        User.objects.create_user('simple', password='Simple-test-123')
        rep = self.client.post('/connexion/', {'username': 'simple', 'password': 'Simple-test-123'})
        self.assertContains(rep, "n&#x27;a pas accès à l&#x27;espace RH")

        User.objects.create_user('rh', password='Rh-test-123', is_staff=True)
        rep = self.client.post('/connexion/', {'username': 'rh', 'password': 'Rh-test-123'})
        self.assertRedirects(rep, '/', fetch_redirect_response=False)

    def test_pages_accessibles_au_staff(self):
        staff = User.objects.create_user('rh', password='Rh-test-123', is_staff=True)
        self.client.force_login(staff)
        departement = Departement.objects.create(nom='Pédagogie', responsable='Awa Diop')
        employe = Employe.objects.create(
            matricule='EMP-001', nom='Diop', prenom='Awa', email='awa@isep-at.sn',
            telephone=771234567, date_embauche=date(2020, 1, 1), poste='Enseignante', departement=departement,
        )
        for url in ['/', '/employes/ajouter/', f'/employes/{employe.id}/',
                    f'/employes/{employe.id}/modifier/', '/departements/']:
            rep = self.client.get(url)
            self.assertEqual(rep.status_code, 200, url)
            self.assertContains(rep, 'bootstrap@5.3.3')
