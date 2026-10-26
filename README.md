# Gestion RH – ISEP-AT

Application de gestion des ressources humaines (Session de certification 2025, métier APD).

- **Backend** : API REST avec Django REST Framework (app `rh`) et PostgreSQL dans Docker.
- **Frontend** : pages Bootstrap 5 servies par Django (app `frontend`) qui consomment l'API en JavaScript (`fetch`).

## Structure

```
Devoire/
├── gestion_rh/
│   ├── manage.py
│   ├── gestion_rh/        # configuration (settings, urls)
│   ├── rh/                # backend : modèles, serializers, API, admin, tests
│   └── frontend/          # frontend : templates Bootstrap + static/frontend/app.js
├── docker-compose.yml     # PostgreSQL 17
├── requirements.txt
└── .env.example
```

## Lancer l'application

Prérequis : Python 3.13 et Docker Desktop (ouvert).

```bash
copy .env.example .env          # puis remplacer les deux « change-moi »
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
docker compose up -d
cd gestion_rh
python manage.py migrate
python manage.py seed_rh          # données de démonstration (facultatif)
python manage.py createsuperuser
python manage.py runserver 8002
```

Ouvrir http://127.0.0.1:8002/ et se connecter avec le compte créé (les pages sont réservées aux comptes staff).

Tests : `python manage.py test rh`

## Modèles

Modèle fourni par le professeur (`rh/models.py`).

| Modèle | Champs |
|---|---|
| `Departement` | nom (unique), description, responsable (texte) |
| `Employe` | matricule, nom, prénom, email, téléphone (nombre), date d'embauche, poste, département (→ Departement, `CASCADE`, `related_name='emplois'`) |
| `Contrat` | référence (unique), type_contrat (CDD / CDI / PRESTATAIRE), date début, date fin, emploi (→ Employe, `PROTECT`, `related_name='contrats'`) |

Les contrats sont saisis dans le même formulaire que l'employé. Comme `Contrat.emploi` est en `PROTECT`, la suppression d'un employé supprime d'abord ses contrats.
Validation (API) : matricule et référence de contrat non dupliqués, date de fin obligatoire pour un CDD ou une prestation et postérieure à la date de début.

## API (backend)

Toutes les routes demandent un compte staff connecté.

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/employes/` | Liste (`?departement=<id>`, `?search=<texte>`) |
| POST | `/api/employes/` | Ajouter un employé avec ses contrats |
| GET | `/api/employes/<id>/` | Fiche d'un employé |
| PUT / PATCH | `/api/employes/<id>/` | Modifier (contrats : ajout, modification, suppression) |
| DELETE | `/api/employes/<id>/` | Supprimer (et ses contrats) |
| GET / POST | `/api/departements/` | Liste / ajout de départements |
| GET / PUT / PATCH / DELETE | `/api/departements/<id>/` | Gérer un département |
| GET | `/api/statistiques/` | Chiffres clés (employés, départements, contrats) |

Exemple de corps pour `POST /api/employes/` :

```json
{
  "matricule": "EMP-009", "nom": "Diallo", "prenom": "Khadija",
  "email": "khadija.diallo@isep-at.sn", "telephone": 775554433,
  "date_embauche": "2026-10-01", "poste": "Enseignante Django", "departement": 1,
  "contrats": [{"reference": "CTR-2026-009", "type_contrat": "CDD", "date_debut": "2026-10-01", "date_fin": "2027-09-30"}]
}
```

## Pages (frontend)

| Page | URL |
|---|---|
| Connexion (comptes staff uniquement) | `/connexion/` |
| Liste des employés (chiffres clés, échéances de contrat, filtre par département, recherche) | `/` |
| Ajouter un employé | `/employes/ajouter/` |
| Fiche d'un employé | `/employes/<id>/` |
| Modifier un employé (formulaire pré-rempli) | `/employes/<id>/modifier/` |
| Départements | `/departements/` |
| Administration Django | `/admin/` |

La suppression se fait depuis la liste ou la fiche : fenêtre de confirmation, puis message de confirmation.
