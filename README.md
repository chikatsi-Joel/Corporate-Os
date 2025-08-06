# Gestion des Actions - API FastAPI

Une application web full-stack pour la gestion des actionnaires et l'émission d'actions, construite avec FastAPI et sécurisée avec Keycloak.

## Fonctionnalités

### Administrateur
-  Connexion sécurisée au système via Keycloak
-  Tableau de bord avec liste des actionnaires et total de leurs actions
-  Visualisation de la répartition des parts (graphique en camembert)
-  Ajout de nouveaux actionnaires
-  Émission d'actions pour les actionnaires existants
-  Génération de certificats PDF filigranés

### Actionnaire
-  Connexion sécurisée au système via Keycloak
-  Tableau de bord personnel avec informations et nombre total d'actions
-  Consultation de toutes les émissions
-  Téléchargement des certificats PDF correspondants

## Architecture

```
├── app/
│   ├── api/           # Endpoints API
│   ├── core/          # Configuration et sécurité
│   ├── crud/          # Opérations base de données
│   ├── database/      # Modèles de données
│   ├── schemas/       # Schémas Pydantic
│   └── services/      # Services métier
├── scripts/           # Scripts utilitaires
├── certificates/      # Certificats PDF générés
├── uploads/          # Fichiers uploadés
└── docker-compose.yml # Configuration Docker complète
```

## Technologies

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Authentification**: Keycloak (OAuth2/OpenID Connect)
- **Base de données**: PostgreSQL (2 instances : app + keycloak)
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Validation**: Pydantic
- **PDF**: ReportLab
- **Containerisation**: Docker, Docker Compose
- **Documentation**: OpenAPI/Swagger

## Installation

### Prérequis

- Docker et Docker Compose
- Python 3.11+ (pour le développement local)
- Git

### 🚀 Installation Rapide avec Docker

1. **Cloner le projet**
```bash
git clone <repository-url>
cd Patrck_S
```

2. **Démarrer avec le script automatique**
```bash
# Installer les dépendances Python pour le script
pip install requests

# Lancer le script de démarrage complet
python scripts/start_with_keycloak.py
```

3. **Ou démarrer manuellement**
```bash
# Démarrer tous les services
docker-compose up -d

# Attendre que les services soient prêts (2-3 minutes)
# Puis configurer Keycloak
python scripts/setup_keycloak.py
```

### 🔧 Installation Locale (Développement)

1. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configurer l'environnement**
```bash
cp env.example .env
# Éditer .env avec vos paramètres
```

4. **Démarrer Keycloak**
```bash
docker-compose up keycloak keycloak-db -d
```

5. **Configurer Keycloak**
```bash
python scripts/setup_keycloak.py
```

6. **Initialiser la base de données**
```bash
python app/database_init.py
```

7. **Lancer l'application**
```bash
python run.py
```

## Documentation API

Une fois l'application lancée, la documentation interactive est disponible sur :
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Authentification

L'application utilise Keycloak pour l'authentification. Pour obtenir un token :

```bash
# Connexion via Keycloak
curl -X POST "http://localhost:8000/api/v1/keycloak/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
```

## Endpoints principaux

### Authentification Keycloak
- `POST /api/v1/keycloak/login` - Connexion
- `GET /api/v1/keycloak/me` - Informations utilisateur
- `GET /api/v1/keycloak/health` - Santé de la connexion

### Utilisateurs
- `GET /api/v1/users/me` - Informations utilisateur connecté
- `GET /api/v1/users/` - Liste des utilisateurs (Admin)
- `GET /api/v1/users/shareholders` - Liste des actionnaires (Admin)

### Actions
- `GET /api/v1/stocks/` - Liste des actions (Admin)
- `POST /api/v1/stocks/` - Créer une action (Admin)
- `GET /api/v1/stocks/my-stocks` - Mes actions (Actionnaire)
- `GET /api/v1/stocks/my-total` - Total de mes actions (Actionnaire)

### Certificats
- `POST /api/v1/certificates/generate/{stock_id}` - Générer un certificat
- `GET /api/v1/certificates/download/{stock_id}` - Télécharger un certificat

## Docker

### Services inclus

Le fichier `docker-compose.yml` inclut :

1. **actions-db** : Base de données PostgreSQL pour l'application
2. **keycloak-db** : Base de données PostgreSQL pour Keycloak
3. **keycloak** : Serveur Keycloak pour l'authentification
4. **actions-app** : Application FastAPI

### Commandes utiles

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter les services
docker-compose down

# Redémarrer un service
docker-compose restart keycloak

# Reconstruire l'application
docker-compose build app
```

### Ports utilisés

- **8000** : Application FastAPI
- **8080** : Interface Keycloak
- **5432** : Base de données application
- **5433** : Base de données Keycloak (interne)

## Tests

```bash
pytest

pytest --cov=app
```

## Structure de la base de données

### Tables principales

- **users** : Utilisateurs du système
- **stocks** : Actions émises
- **shareholders** : Actionnaires
- **admins** : Administrateurs

### Relations

- Chaque action appartient à un actionnaire
- Les utilisateurs peuvent être admin ou actionnaire

## Migrations

```bash
alembic revision --autogenerate -m "Description"

alembic upgrade head

alembic downgrade -1
```

## Déploiement

### Production

1. **Configurer les variables d'environnement**
```env
DATABASE_URL=postgresql://user:password@host:5432/actions_db
KEYCLOAK_SERVER_URL=https://keycloak.yourdomain.com
KEYCLOAK_CLIENT_SECRET=your-secure-client-secret
SECRET_KEY=your-secure-secret-key
```

2. **Déployer avec Docker**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Support

Pour toute question ou problème :
1. Vérifier la documentation
2. Consulter les issues existantes
3. Créer une nouvelle issue avec les détails du problème
