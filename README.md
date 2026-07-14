Parfait, voici la marche à suivre :

Ouvre le fichier dans VS Code :

powershellcode README.md

Sélectionne tout (Ctrl+A) et supprime le contenu existant
Colle le contenu ci-dessous (copie tout le bloc, du # MediRDV Agent jusqu'à la toute dernière ligne)
Sauvegarde (Ctrl+S)

markdown# MediRDV Agent 🩺🤖

Assistant conversationnel de prise de rendez-vous médicaux, propulsé par un
agent IA (Claude + LangChain avec function calling), avec espace patient et
dashboard administrateur.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Gestion des praticiens](#gestion-des-praticiens)
- [Espace admin](#espace-admin)
- [Tests](#tests)
- [Structure du projet](#structure-du-projet)

## Fonctionnalités

**Agent conversationnel**
- 💬 Chat en français pour consulter les disponibilités, réserver, annuler ou
  reprogrammer un rendez-vous
- 🤖 Agent Claude avec function calling (6 outils : lister les praticiens,
  vérifier les disponibilités par praticien/spécialité, réserver, annuler,
  reprogrammer, consulter l'historique d'un patient)
- 📅 Empêche le double-booking au niveau base de données

**Comptes et sécurité**
- 📝 Inscription patient avec vérification d'email par code à 6 chiffres
- 🔐 Connexion (JWT), mots de passe hashés (bcrypt)
- 👤 Espace patient : consultation de son propre historique de rendez-vous
- 🛡️ Compte admin séparé (rôle dédié), routes protégées

**Notifications**
- 📧 Emails réels (SMTP) : confirmation, annulation, rappel automatique 24h
  avant le rendez-vous (scheduler en arrière-plan, vérification toutes les
  heures)

**Espace admin**
- 📊 Dashboard avec statistiques (total, confirmés, annulés, taux
  d'annulation, activité des 7 derniers jours) et liste de tous les
  rendez-vous
- 📄 Export CSV et PDF des rendez-vous, avec en-tête personnalisable (nom
  d'établissement + logo)

**Infra**
- 🐳 Entièrement conteneurisé (Docker Compose : PostgreSQL, backend,
  frontend, Adminer)
- ✅ 40 tests automatisés (pytest) sur la logique métier critique

## Architecture
┌─────────────┐      HTTP       ┌──────────────┐      SQL       ┌─────────────┐
│   Frontend   │ ─────────────► │   Backend    │ ─────────────► │  PostgreSQL │
│ React + Vite │ ◄───────────── │   FastAPI    │ ◄───────────── │             │
└─────────────┘                 └──────┬───────┘                └─────────────┘
│
│ function calling
▼
┌──────────────┐
│  Claude API  │
│  (Anthropic) │
└──────────────┘

Le frontend propose deux espaces : le **chat patient** (accessible à tous,
compte optionnel) et l'**espace admin** (connexion requise, rôle admin).

## Stack technique

**Backend** : Python 3.12, FastAPI, SQLAlchemy, PostgreSQL, LangChain +
langchain-anthropic (Claude), APScheduler, bcrypt, PyJWT, ReportLab, pytest

**Frontend** : React 18, Vite (vanilla, pas de framework CSS)

**Infra** : Docker, Docker Compose, Adminer

## Prérequis

- Docker Desktop installé et lancé
- Une clé API Anthropic (console.anthropic.com)
- (Optionnel, pour les emails) Un compte Gmail avec un mot de passe
  d'application

## Installation

1. **Cloner le repo et configurer l'environnement**
```bash
   git clone <url-du-repo>
   cd medirdv-agent
   cp backend/.env.example backend/.env
```

2. **Éditer `backend/.env`**
```env
   ANTHROPIC_API_KEY=sk-ant-votre-cle-ici
   DATABASE_URL=postgresql://medirdv_user:medirdv_password@db:5432/medirdv_db
   APP_ENV=development
   JWT_SECRET_KEY=change-moi-en-une-vraie-valeur-secrete

   # Optionnel : notifications email reelles
   SMTP_USER=votre_adresse@gmail.com
   SMTP_PASSWORD=votre_mot_de_passe_application
   SMTP_FROM=votre_adresse@gmail.com

   # Optionnel : personnalisation des exports CSV/PDF
   CLINIC_NAME=MediRDV
   CLINIC_LOGO_PATH=app/static/logo.png
```

3. **Lancer la stack complète**
```bash
   docker compose up --build
```

4. **Peupler la base avec des données de test**
```bash
   docker compose exec backend python -m app.seed
```

5. **Accéder à l'application**
   - Chat patient : http://localhost:5173
   - Documentation API interactive : http://localhost:8000/docs
   - Adminer (visualisation base de données) : http://localhost:8080

## Utilisation

Ouvre http://localhost:5173 et discute avec l'assistant :

> "Bonjour, je voudrais un rendez-vous avec un cardiologue"

L'agent cherche les disponibilités, les propose, demande nom/email, réserve,
et envoie un email de confirmation. Pour reprogrammer ou annuler, il suffit
de le demander en langage naturel dans la même conversation.

### Créer un compte patient (optionnel)

`POST /auth/register` → réception d'un code à 6 chiffres par email →
`POST /auth/verify` → `POST /auth/login` pour obtenir un token JWT →
`GET /appointments/me` pour consulter son propre historique.

### Endpoints principaux

| Méthode | Endpoint                  | Description                              | Auth requise |
|---------|----------------------------|-------------------------------------------|--------------|
| GET     | /practitioners/             | Liste des praticiens                      | non |
| GET     | /slots/available             | Créneaux disponibles (filtrables)         | non |
| POST    | /appointments/               | Créer un rendez-vous                      | non |
| DELETE  | /appointments/{id}            | Annuler un rendez-vous                    | oui (proprietaire ou admin) |
| GET     | /appointments/me              | Historique du patient connecté            | oui |
| POST    | /chat/                       | Discuter avec l'agent IA                  | non |
| POST    | /auth/register                | Créer un compte patient                   | non |
| POST    | /auth/verify                  | Vérifier l'email (code)                   | non |
| POST    | /auth/login                   | Connexion (retourne un token JWT)         | non |
| GET     | /admin/stats                  | Statistiques globales                     | oui (admin) |
| GET     | /admin/appointments            | Tous les rendez-vous                      | oui (admin) |
| GET     | /admin/export/csv              | Export CSV                                | oui (admin) |
| GET     | /admin/export/pdf              | Export PDF                                 | oui (admin) |
| POST    | /reminders/run                 | Déclencher les rappels manuellement       | non |

## Gestion des praticiens

```bash
# Ajouter un nouveau praticien (avec ses creneaux sur X jours, 14 par defaut)
docker compose exec backend python -m app.manage_practitioners add "Dr. Nom Complet" "Specialite" --days 30

# Prolonger les creneaux d'un praticien existant
docker compose exec backend python -m app.manage_practitioners extend "Dr. Nom" --days 30

# Prolonger les creneaux de TOUS les praticiens
docker compose exec backend python -m app.manage_practitioners extend-all --days 30
```

## Espace admin

Promouvoir un compte patient existant (déjà inscrit et vérifié) en admin :
```bash
docker compose exec backend python -m app.make_admin ton_email@exemple.com
```

Se reconnecter ensuite (`POST /auth/login`) pour obtenir un token à jour, puis
accéder au dashboard sur http://localhost:5173 → "Espace admin".

## Tests

```bash
docker compose exec backend pytest -v
```

40 tests couvrent : réservation, double-booking, annulation, reprogrammation,
filtrage par spécialité, historique, inscription/vérification, connexion,
statistiques admin, exports CSV/PDF.

## Structure du projet
medirdv-agent/
├── backend/
│   ├── app/
│   │   ├── agent/              # Agent LangChain + tools (function calling)
│   │   ├── routers/             # Endpoints FastAPI (auth, admin, appointments...)
│   │   ├── services/            # Logique metier (scheduling, email, auth, export...)
│   │   ├── static/               # Logo pour les exports (optionnel)
│   │   ├── auth_dependencies.py  # Protection des routes (JWT)
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── scheduler.py          # Rappels automatiques
│   │   ├── seed.py
│   │   ├── make_admin.py         # Script : promouvoir un compte en admin
│   │   └── manage_practitioners.py  # Script : ajouter/prolonger les praticiens
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ChatView.jsx
│       │   ├── AdminLogin.jsx
│       │   └── AdminDashboard.jsx
│       └── App.jsx
└── docker-compose.yml

## Notes

Ce projet a été développé dans le cadre d'un stage, comme exercice
d'apprentissage sur l'intégration d'un LLM avec function calling dans une
application full-stack réelle (authentification, rôles, notifications,
exports, dashboard).