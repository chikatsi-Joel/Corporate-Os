# Corporate OS - Gestion de Cap Table

Application de gestion de table de capitalisation (Cap Table) avec authentification Keycloak et génération de certificats PDF.

## 🎯 Objectif

Cette application permet de gérer la table de capitalisation d'une entreprise et d'émettre des actions avec les fonctionnalités suivantes :

- **Administrateur** : Gestion des actionnaires, émission d'actions, visualisation de la Cap Table
- **Actionnaire** : Consultation de ses actions et téléchargement de certificats

## 🏗️ Architecture

### Backend (FastAPI + PostgreSQL + Keycloak)
- **Framework** : FastAPI
- **Base de données** : PostgreSQL
- **Authentification** : Keycloak
- **Génération PDF** : ReportLab
- **Tests** : pytest

### Services Docker
- PostgreSQL (Base de données)
- Keycloak (Authentification)
- FastAPI (Application backend)

## 🚀 Installation et Démarrage

### Prérequis
- Docker et Docker Compose
- Python 3.10+ (pour le développement local)

### 1. Cloner le projet
```bash
git clone <repository-url>
cd Corporate-Os
```

### 2. Configuration Keycloak
L'application utilise Keycloak pour l'authentification avec :
- **Realm** : `corporate-os`
- **Client** : `corporate-os-client`
- **Utilisateurs par défaut** :
  - Admin : `admin` / `admin123`
  - Actionnaire : `actionnaire` / `actionnaire123`

### 3. Démarrage avec Docker Compose
```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier que tous les services sont démarrés
docker-compose ps
```

### 4. Accès aux services
- **Application API** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **Keycloak Admin** : http://localhost:8080 (admin/admin)
- **Base de données** : localhost:5432

## 📚 API Endpoints

### Authentification
- `GET /api/auth/me` - Informations de l'utilisateur connecté
- `GET /api/auth/profile` - Profil complet de l'utilisateur

### Actionnaires (Admin uniquement)
- `GET /api/shareholders/` - Liste des actionnaires avec total des actions
- `POST /api/shareholders/` - Créer un nouvel actionnaire
- `GET /api/shareholders/{id}` - Détails d'un actionnaire
- `GET /api/shareholders/{id}/summary` - Résumé des actions d'un actionnaire

### Émissions d'actions
- `GET /api/issuances/` - Liste des émissions (Admin: toutes, Actionnaire: ses propres)
- `POST /api/issuances/` - Créer une émission (Admin uniquement)
- `GET /api/issuances/{id}` - Détails d'une émission
- `GET /api/issuances/{id}/certificate` - Télécharger le certificat PDF
- `GET /api/issuances/cap-table/summary` - Résumé de la Cap Table (Admin uniquement)

### Audit (Admin uniquement)
- `GET /api/audit/events` - Liste des événements d'audit
- `GET /api/audit/events/{id}` - Détails d'un événement d'audit
- `GET /api/audit/events/types` - Types d'événements disponibles

## 🔧 Développement Local

### Installation des dépendances
```bash
pip install -r requirements.txt
```

### Configuration de l'environnement
Créer un fichier `.env` :
```env
DATABASE_URL=postgresql://corporate_user:corporate_password@localhost:5432/corporate_os
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=corporate-os
KEYCLOAK_CLIENT_ID=corporate-os-client
KEYCLOAK_CLIENT_SECRET=your-client-secret
SECRET_KEY=your-secret-key-here
```

### Migrations de base de données
```bash
# Créer une nouvelle migration
alembic revision --autogenerate -m "Description de la migration"

# Appliquer les migrations
alembic upgrade head
```

### Tests
```bash
# Lancer tous les tests
pytest

# Lancer les tests avec couverture
pytest --cov=app

# Lancer un test spécifique
pytest tests/test_issuance_service.py::TestIssuanceService::test_create_issuance
```

## 🛠️ Outils IA Utilisés

### Backend
- **Cursor** : Assistant IA pour le développement
- **GitHub Copilot** : Suggestions de code en temps réel

### Prompts Utilisés

#### Architecture et Structure
```
"Créer une application FastAPI avec Keycloak pour l'authentification, PostgreSQL pour la base de données, et une architecture en couches (models, services, api)"
```

#### Modèles de Données
```
"Créer les modèles SQLAlchemy pour une application de gestion de Cap Table avec utilisateurs, actionnaires, émissions d'actions et événements d'audit"
```

#### Services Métier
```
"Implémenter un service d'émission d'actions avec calcul automatique du montant total et génération de certificats PDF"
```

#### Authentification Keycloak
```
"Intégrer Keycloak avec FastAPI pour l'authentification JWT et la gestion des rôles admin/actionnaire"
```

## 📊 Structures de Données

### Utilisateur
```json
{
  "id": "uuid",
  "keycloak_id": "string",
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "admin|actionnaire",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Émission d'Actions
```json
{
  "id": "uuid",
  "shareholder_id": "uuid",
  "number_of_shares": "integer",
  "price_per_share": "decimal",
  "total_amount": "decimal",
  "issue_date": "date",
  "status": "issued|pending|cancelled",
  "certificate_path": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Cap Table Summary
```json
{
  "total_shares": "integer",
  "total_value": "decimal",
  "shareholders": [
    {
      "username": "string",
      "first_name": "string",
      "last_name": "string",
      "shares": "integer",
      "value": "decimal",
      "percentage": "decimal"
    }
  ]
}
```

## 🔒 Sécurité

- **Authentification** : Keycloak avec JWT
- **Autorisation** : Rôles admin/actionnaire
- **Validation** : Pydantic pour la validation des données
- **Audit** : Journalisation de tous les événements critiques
- **Certificats** : PDF filigranés pour les émissions d'actions

## 📝 Fonctionnalités Bonus Implémentées

- ✅ **Journalisation** : Événements d'audit complets
- ✅ **Validation avancée** : Contrôles sur les émissions d'actions
- ✅ **Génération PDF** : Certificats avec filigrane
- ✅ **Tests unitaires** : Couverture des services critiques
- ✅ **Migrations** : Alembic pour la gestion des schémas

## 🚀 Améliorations Futures

1. **Notifications email** : Envoi automatique après émission
2. **API GraphQL** : Alternative à REST pour les requêtes complexes
3. **Cache Redis** : Amélioration des performances
4. **Monitoring** : Prometheus + Grafana
5. **CI/CD** : Pipeline automatisé avec tests

## 📞 Support

Pour toute question ou problème :
- Créer une issue sur GitHub
- Contacter l'équipe de développement

## 📄 Licence

Ce projet est développé pour le test technique Corporate OS. 