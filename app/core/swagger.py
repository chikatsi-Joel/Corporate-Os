"""
Configuration personnalisée pour Swagger/OpenAPI
"""

from fastapi.openapi.utils import get_openapi
from typing import Dict, Any


def custom_openapi_schema(app) -> Dict[str, Any]:
    """
    Génère un schéma OpenAPI personnalisé avec des métadonnées enrichies
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
    )
    
    # Ajouter des informations supplémentaires
    openapi_schema["info"]["x-logo"] = {
        "url": "https://corporate-os.com/logo.png",
        "altText": "Corporate OS Logo"
    }
    
    # Configuration des composants de sécurité
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Token JWT obtenu via Keycloak. Format: Bearer <token>"
        }
    }
    
    # Appliquer la sécurité par défaut
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    # Ajouter des exemples de réponses globales
    openapi_schema["components"]["examples"] = {
        "UserExample": {
            "summary": "Exemple d'utilisateur",
            "value": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "john.doe",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "admin",
                "keycloak_id": "keycloak-user-123",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        "IssuanceExample": {
            "summary": "Exemple d'émission d'actions",
            "value": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "shareholder_id": "123e4567-e89b-12d3-a456-426614174001",
                "number_of_shares": 1000,
                "price_per_share": 50.00,
                "total_amount": 50000.00,
                "issue_date": "2024-01-01",
                "status": "issued",
                "certificate_path": "/certificates/issuance_123.pdf",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        "ErrorExample": {
            "summary": "Exemple d'erreur",
            "value": {
                "detail": "Token invalide ou expiré"
            }
        }
    }
    
    # Ajouter des informations sur les codes de statut
    openapi_schema["components"]["responses"] = {
        "UnauthorizedError": {
            "description": "Token d'authentification invalide ou expiré",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Token invalide ou expiré"
                            }
                        }
                    }
                }
            }
        },
        "ForbiddenError": {
            "description": "Accès refusé - permissions insuffisantes",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Accès refusé"
                            }
                        }
                    }
                }
            }
        },
        "NotFoundError": {
            "description": "Ressource non trouvée",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "Ressource non trouvée"
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Ajouter des informations sur les tags
    openapi_schema["tags"] = [
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
            "name": "health",
            "description": "Points de contrôle de santé de l'application et informations système.",
        },
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def get_swagger_ui_parameters() -> Dict[str, Any]:
    """
    Retourne les paramètres personnalisés pour l'interface Swagger UI
    """
    return {
        "swagger_ui_parameters": {
            "defaultModelsExpandDepth": -1,
            "defaultModelExpandDepth": 3,
            "defaultModelRendering": "example",
            "displayRequestDuration": True,
            "docExpansion": "list",
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "tryItOutEnabled": True,
            "syntaxHighlight.theme": "monokai",
            "persistAuthorization": True,
        }
    } 