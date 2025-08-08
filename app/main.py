from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.swagger import custom_openapi_schema, get_swagger_ui_parameters
from app.database.database import engine
from app.database import models
from fastapi_keycloak_middleware import KeycloakConfiguration, setup_keycloak_middleware, AuthorizationMethod
from app.api import auth, shareholders, issuances
import logging
import typing
#from ..audit.api.audit_api import router

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer les tables
models.Base.metadata.create_all(bind=engine)

# Démarrer le bus d'événements
try:
    from bus_event.events import event_bus
    event_bus.start()
    logger.info("Bus d'événements démarré avec succès")
except Exception as e:
    logger.error(f"Erreur lors du démarrage du bus d'événements: {e}")

# Métadonnées pour l'API
tags_metadata = [
    {
        "name": "authentication",
        "description": "Opérations d'authentification et de gestion des utilisateurs. Utilise Keycloak pour l'authentification JWT.",
        "externalDocs": {
            "description": "Documentation Keycloak",
            "url": "https://www.keycloak.org/documentation",
        },
    },
    {
        "name": "shareholders",
        "description": "Gestion des actionnaires. Permet de créer, consulter et gérer les actionnaires de l'entreprise.",
    },
    {
        "name": "issuances",
        "description": "Gestion des émissions d'actions. Permet de créer des émissions, consulter les certificats et gérer la Cap Table.",
    },
    {
        "name": "notifications",
        "description": "Gestion des notifications. Permet d'envoyer et de gérer les notifications aux utilisateurs.",
    },
    {
        "name": "audit",
        "description": "Gestion des événements d'audit. Permet de tracer et d'analyser les actions des utilisateurs.",
    },
    {
        "name": "health",
        "description": "Points de contrôle de santé de l'application et informations système.",
    },
]

# Créer l'application FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
# Corporate OS - API de Gestion de Cap Table

## Description

Cette API permet de gérer la table de capitalisation (Cap Table) d'une entreprise avec les fonctionnalités suivantes :

### Fonctionnalités Principales

* ** Authentification** : Intégration avec Keycloak pour l'authentification JWT
* ** Gestion des Actionnaires** : Création et gestion des actionnaires
* ** Émissions d'Actions** : Gestion des émissions d'actions avec calcul automatique
* ** Certificats PDF** : Génération automatique de certificats d'actions
* ** Cap Table** : Visualisation et gestion de la table de capitalisation
* ** Notifications** : Système de notifications pour les événements importants
* ** Audit** : Traçabilité complète des actions utilisateurs

### Rôles Utilisateurs

* **Admin** : Accès complet à toutes les fonctionnalités
* **Actionnaire** : Consultation de ses propres actions et certificats

### Technologies Utilisées

* **Framework** : FastAPI
* **Base de données** : PostgreSQL
* **Authentification** : Keycloak
* **Génération PDF** : ReportLab
* **Message Broker** : RabbitMQ
* **Documentation** : Swagger/OpenAPI

## Démarrage Rapide

1. **Démarrer les services** : `docker-compose up -d`
2. **Accéder à la documentation** : http://localhost:8000/docs
3. **Authentification** : Utiliser Keycloak (http://localhost:8080)
4. **RabbitMQ Management** : http://localhost:15672

## Endpoints Principaux

* `GET /` - Point d'entrée de l'application
* `GET /health` - Contrôle de santé
* `GET /api/auth/me` - Informations utilisateur connecté
* `GET /api/shareholders/` - Liste des actionnaires
* `GET /api/issuances/` - Liste des émissions
* `GET /api/issuances/cap-table/summary` - Résumé de la Cap Table
* `GET /api/audit/events` - Événements d'audit (admin uniquement)

## 🔒 Authentification

L'API utilise Keycloak pour l'authentification. Tous les endpoints (sauf `/` et `/health`) nécessitent un token JWT valide.

### Utilisateurs par défaut :
* **Admin** : `admin` / `admin123`
* **Actionnaire** : `actionnaire` / `actionnaire123`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    tags_metadata=tags_metadata,
    contact={
        "name": "Support Corporate OS",
        "email": "support@corporate-os.com",
        "url": "https://corporate-os.com/support",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Serveur de développement"
        },
        {
            "url": "https://api.corporate-os.com",
            "description": "Serveur de production"
        }
    ],
    **get_swagger_ui_parameters()
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

excluded_routes = [
    "/status",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/auth/login"
]

async def map_user(userinfo: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
   return userinfo

import time

#Le temps que keycloak démarre
time.sleep(40)  
config = KeycloakConfiguration(
    url=settings.keycloak_url,
    realm=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
    client_secret=settings.keycloak_client_secret,
    claims=[
        "sub", 
        "name", 
        "email", 
        "preferred_username", 
        "given_name", 
        "family_name",
        "realm_access"
    ]
)

setup_keycloak_middleware(app, config, user_mapper=map_user, exclude_patterns=excluded_routes)

# Inclure les routes
app.include_router(auth.router)
app.include_router(shareholders.router)
app.include_router(issuances.router)
#app.include_router(router)

# Configuration personnalisée de l'OpenAPI schema
app.openapi = lambda: custom_openapi_schema(app)


@app.get("/", tags=["health"])
async def root():
    """
    Point d'entrée de l'application
    
    Retourne les informations de base de l'application et les liens vers la documentation.
    """
    return {
        "message": "Bienvenue dans Corporate OS - Gestion de Cap Table",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/health"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Point de contrôle de santé de l'application
    
    Utilisé par les systèmes de monitoring pour vérifier que l'application fonctionne correctement.
    """
    return {
        "status": "healthy", 
        "service": "corporate-os",
        "version": settings.app_version,
        "timestamp": "2024-01-01T00:00:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)