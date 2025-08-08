# Corporate OS - Plateforme de Gestion de Cap Table

## 🎯 Objectif du Projet

Corporate OS est une plateforme moderne de gestion de table de capitalisation (Cap Table) conçue pour les entreprises en croissance. Elle permet de gérer les actionnaires, les émissions d'actions, et de générer automatiquement des certificats d'actions tout en assurant une traçabilité complète des opérations.

## 🏗️ Architecture Technique

### **Pourquoi cette stack technologique ?**

#### **Backend - FastAPI**
- **Performance** : FastAPI est l'un des frameworks Python les plus rapides, basé sur Starlette et Pydantic
- **Type Safety** : Validation automatique des types avec Pydantic, réduisant les bugs en production
- **Documentation Auto-générée** : OpenAPI/Swagger intégré, facilitant l'intégration et les tests
- **Async/Await** : Support natif de l'asynchrone pour une meilleure performance sous charge
- **Écosystème Riche** : Large communauté et nombreuses intégrations disponibles

#### **Base de Données - PostgreSQL**
- **ACID Compliance** : Garantit l'intégrité des données financières critiques
- **Performance** : Excellent pour les requêtes complexes et les jointures
- **JSON Support** : Stockage flexible des métadonnées et configurations
- **Scalabilité** : Support des grandes volumes de données et de la réplication
- **Open Source** : Coût réduit et contrôle total sur l'infrastructure

#### **Authentification - Keycloak**
- **Enterprise Ready** : Solution d'identité et d'accès (IAM) de niveau entreprise
- **Standards Ouverts** : Support OAuth2, OpenID Connect, SAML
- **Gestion des Rôles** : Système de rôles et permissions sophistiqué
- **SSO** : Single Sign-On pour une expérience utilisateur fluide
- **Sécurité** : Audit trail complet, MFA, gestion des sessions

#### **Containerisation - Docker & Docker Compose**
- **Reproductibilité** : Environnements identiques en dev, staging et production
- **Isolation** : Chaque service fonctionne dans son propre conteneur
- **Scalabilité** : Déploiement facile sur différents environnements
- **DevOps** : Intégration continue et déploiement continu simplifiés
- **Portabilité** : Fonctionne sur n'importe quelle plateforme supportant Docker

#### **Bus d'Événements - Système Custom**
- **Légèreté** : Pas de dépendance externe lourde comme RabbitMQ
- **Performance** : Traitement asynchrone sans overhead réseau
- **Simplicité** : Décorateurs Python pour une utilisation intuitive
- **Flexibilité** : Adapté aux besoins spécifiques du projet
- **Maintenance** : Code source contrôlé et facilement modifiable

#### **Génération PDF - ReportLab**
- **Performance** : Génération rapide de documents complexes
- **Flexibilité** : Contrôle total sur la mise en page et le design
- **Sécurité** : Possibilité d'ajouter des filigranes et signatures
- **Standards** : Support des formats PDF/A pour l'archivage
- **Python Native** : Intégration parfaite avec l'écosystème Python

#### **ORM - SQLAlchemy**
- **Productivité** : Mapping objet-relationnel puissant
- **Performance** : Query builder optimisé et lazy loading
- **Flexibilité** : Support des requêtes natives et des migrations
- **Type Safety** : Intégration avec les types Python
- **Écosystème** : Large communauté et nombreuses extensions

#### **Validation - Pydantic**
- **Type Safety** : Validation automatique des données
- **Performance** : Validation rapide basée sur Rust (Pydantic v2)
- **Documentation** : Génération automatique de schémas OpenAPI
- **Intégration** : Parfaitement intégré avec FastAPI
- **Extensibilité** : Validateurs personnalisés faciles à créer

## 🚀 Installation et Démarrage

### Prérequis
- Docker et Docker Compose
- Git
- 4GB RAM minimum

### Démarrage Rapide
```bash
# Cloner le projet
git clone https://github.com/votre-org/corporate-os.git
cd corporate-os

# Copier le fichier d'environnement
cp .env.example .env

# Démarrer les services
docker compose up -d

# Vérifier le statut
docker compose ps
```

### Accès aux Services
- **Application** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **Keycloak Admin** : http://localhost:8080 (admin/admin)
- **Base de données** : localhost:5432

## 📊 Fonctionnalités Principales

### **Gestion des Actionnaires**
- Création et gestion des profils d'actionnaires
- Validation automatique des données
- Historique complet des modifications
- Export des données en différents formats

### **Émissions d'Actions**
- Calcul automatique des montants
- Génération de certificats PDF
- Validation des règles métier
- Traçabilité complète des opérations

### **Système d'Audit**
- Journalisation de toutes les actions
- Persistance en base de données
- Recherche et filtrage avancés
- Export des rapports d'audit

### **Gestion des Certificats**
- Génération automatique de certificats PDF
- Stockage sécurisé des documents
- Téléchargement en base64
- Versioning des certificats

## 🔐 Sécurité et Conformité

### **Authentification et Autorisation**
- **Keycloak** : Gestion centralisée des identités
- **JWT** : Tokens sécurisés et éphémères
- **RBAC** : Contrôle d'accès basé sur les rôles
- **Audit Trail** : Traçabilité complète des accès

### **Protection des Données**
- **Chiffrement** : Données sensibles chiffrées
- **Validation** : Validation stricte des entrées
- **Sanitisation** : Protection contre les injections
- **Backup** : Sauvegarde automatique des données

### **Conformité**
- **GDPR** : Respect du règlement européen
- **SOX** : Conformité pour les entreprises publiques
- **Audit** : Journalisation pour les audits externes
- **Archivage** : Conservation des données selon la réglementation

## 🧪 Tests et Qualité

### **Tests Unitaires**
```bash
# Lancer les tests
docker compose exec app pytest

# Tests avec couverture
docker compose exec app pytest --cov=app

# Tests spécifiques
docker compose exec app pytest tests/test_audit.py -v
```

### **Tests d'Intégration**
- Tests des endpoints API
- Tests de la base de données
- Tests d'authentification
- Tests de génération de certificats

### **Qualité du Code**
- **Black** : Formatage automatique du code
- **Flake8** : Linting et détection d'erreurs
- **MyPy** : Vérification des types
- **Pre-commit** : Hooks de validation

## 📈 Monitoring et Observabilité

### **Logging**
- **Structured Logging** : Logs JSON pour faciliter l'analyse
- **Niveaux de Log** : DEBUG, INFO, WARNING, ERROR
- **Correlation IDs** : Traçabilité des requêtes
- **Centralisation** : Agrégation des logs

### **Métriques**
- **Performance** : Temps de réponse des endpoints
- **Erreurs** : Taux d'erreur et types d'erreurs
- **Utilisation** : Nombre de requêtes et utilisateurs
- **Ressources** : CPU, mémoire, disque

### **Alerting**
- **Seuils** : Alertes automatiques sur les métriques
- **Escalade** : Notifications aux équipes
- **Dashboard** : Visualisation en temps réel

## 🔄 CI/CD et Déploiement

### **Pipeline d'Intégration**
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

### **Déploiement**
- **Staging** : Environnement de pré-production
- **Production** : Déploiement automatisé
- **Rollback** : Retour en arrière rapide
- **Blue-Green** : Déploiement sans interruption

## 🛠️ Développement

### **Structure du Projet**
```
corporate-os/
├── app/                    # Application FastAPI
│   ├── api/               # Endpoints API
│   ├── core/              # Configuration et utilitaires
│   ├── database/          # Modèles et migrations
│   ├── services/          # Logique métier
│   └── schemas/           # Modèles Pydantic
├── core/                  # Modules partagés
│   └── events/            # Système d'événements
├── alembic/               # Migrations de base de données
├── docker/                # Configuration Docker
└── tests/                 # Tests unitaires et d'intégration
```

### **Commandes Utiles**
```bash
# Démarrer en mode développement
docker compose -f docker-compose.dev.yml up

# Créer une migration
docker compose exec app alembic revision --autogenerate -m "Description"

# Appliquer les migrations
docker compose exec app alembic upgrade head

# Redémarrer un service
docker compose restart app

# Voir les logs
docker compose logs -f app
```

## 📚 Documentation

### **API Documentation**
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
- **OpenAPI** : http://localhost:8000/openapi.json

### **Documentation Technique**
- **Architecture** : [docs/architecture.md](docs/architecture.md)
- **API Reference** : [docs/api.md](docs/api.md)
- **Deployment** : [docs/deployment.md](docs/deployment.md)
- **Troubleshooting** : [docs/troubleshooting.md](docs/troubleshooting.md)

## 🤝 Contribution

### **Guidelines**
1. **Fork** le projet
2. **Créer** une branche feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** les changements (`git commit -m 'Add AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. **Ouvrir** une Pull Request

### **Standards de Code**
- **PEP 8** : Style de code Python
- **Type Hints** : Annotations de types obligatoires
- **Docstrings** : Documentation des fonctions
- **Tests** : Couverture de code > 80%

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🆘 Support

### **Communauté**
- **Issues** : [GitHub Issues](https://github.com/votre-org/corporate-os/issues)
- **Discussions** : [GitHub Discussions](https://github.com/votre-org/corporate-os/discussions)
- **Wiki** : [Documentation Wiki](https://github.com/votre-org/corporate-os/wiki)

### **Contact**
- **Email** : support@corporate-os.com
- **Slack** : [Corporate OS Community](https://corporate-os.slack.com)
- **Documentation** : [docs.corporate-os.com](https://docs.corporate-os.com)

---

**Corporate OS** - Simplifiez la gestion de votre Cap Table 🚀 