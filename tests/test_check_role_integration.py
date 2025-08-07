import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.core.check_role import (
    get_current_user,
    require_role,
    require_any_role,
    require_all_roles
)


class TestCheckRoleIntegration:
    """Tests d'intégration pour les fonctions de vérification des rôles avec FastAPI"""

    @pytest.fixture
    def app(self):
        """Fixture pour créer une application FastAPI de test"""
        app = FastAPI()
        
        @app.get("/test-get-current-user")
        async def test_get_current_user_endpoint(current_user = Depends(get_current_user)):
            return {"user": current_user}
        
        @app.get("/test-require-role-admin")
        async def test_require_role_admin_endpoint(current_user = Depends(require_role("admin"))):
            return {"message": "Admin access granted", "user": current_user}
        
        @app.get("/test-require-any-role")
        async def test_require_any_role_endpoint(current_user = Depends(require_any_role(["admin", "actionnaire"]))):
            return {"message": "Role access granted", "user": current_user}
        
        @app.get("/test-require-all-roles")
        async def test_require_all_roles_endpoint(current_user = Depends(require_all_roles(["admin", "actionnaire"]))):
            return {"message": "All roles access granted", "user": current_user}
        
        return app

    @pytest.fixture
    def client(self, app):
        """Fixture pour créer un client de test"""
        return TestClient(app)

    @pytest.fixture
    def admin_user(self):
        """Fixture pour un utilisateur admin"""
        return {
            "sub": "123",
            "preferred_username": "admin",
            "email": "admin@example.com",
            "realm_access": {
                "roles": ["admin", "user"]
            }
        }

    @pytest.fixture
    def actionnaire_user(self):
        """Fixture pour un utilisateur actionnaire"""
        return {
            "sub": "456",
            "preferred_username": "actionnaire",
            "email": "actionnaire@example.com",
            "realm_access": {
                "roles": ["actionnaire", "user"]
            }
        }

    @pytest.fixture
    def user_without_roles(self):
        """Fixture pour un utilisateur sans rôles"""
        return {
            "sub": "789",
            "preferred_username": "user",
            "email": "user@example.com",
            "realm_access": {
                "roles": []
            }
        }

    @pytest.mark.asyncio
    async def test_get_current_user_endpoint_success(self, client, admin_user):
        """Test d'intégration pour l'endpoint get_current_user avec succès"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user
            
            response = client.get("/test-get-current-user")
            
            assert response.status_code == 200
            assert response.json()["user"] == admin_user

    @pytest.mark.asyncio
    async def test_get_current_user_endpoint_failure(self, client):
        """Test d'intégration pour l'endpoint get_current_user avec échec"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = None
            
            response = client.get("/test-get-current-user")
            
            assert response.status_code == 401
            assert response.json()["detail"] == "User not authenticated"

    @pytest.mark.asyncio
    async def test_require_role_admin_success(self, client, admin_user):
        """Test d'intégration pour l'endpoint require_role avec succès"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user
            
            response = client.get("/test-require-role-admin")
            
            assert response.status_code == 200
            assert response.json()["message"] == "Admin access granted"
            assert response.json()["user"] == admin_user

    @pytest.mark.asyncio
    async def test_require_role_admin_failure(self, client, actionnaire_user):
        """Test d'intégration pour l'endpoint require_role avec échec"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = actionnaire_user
            
            response = client.get("/test-require-role-admin")
            
            assert response.status_code == 403
            assert response.json()["detail"] == "Role 'admin' is required"

    @pytest.mark.asyncio
    async def test_require_any_role_success_admin(self, client, admin_user):
        """Test d'intégration pour l'endpoint require_any_role avec succès (admin)"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user
            
            response = client.get("/test-require-any-role")
            
            assert response.status_code == 200
            assert response.json()["message"] == "Role access granted"
            assert response.json()["user"] == admin_user

    @pytest.mark.asyncio
    async def test_require_any_role_success_actionnaire(self, client, actionnaire_user):
        """Test d'intégration pour l'endpoint require_any_role avec succès (actionnaire)"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = actionnaire_user
            
            response = client.get("/test-require-any-role")
            
            assert response.status_code == 200
            assert response.json()["message"] == "Role access granted"
            assert response.json()["user"] == actionnaire_user

    @pytest.mark.asyncio
    async def test_require_any_role_failure(self, client, user_without_roles):
        """Test d'intégration pour l'endpoint require_any_role avec échec"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = user_without_roles
            
            response = client.get("/test-require-any-role")
            
            assert response.status_code == 403
            assert response.json()["detail"] == "One of these roles is required: admin, actionnaire"

    @pytest.mark.asyncio
    async def test_require_all_roles_success(self, client):
        """Test d'intégration pour l'endpoint require_all_roles avec succès"""
        user_with_all_roles = {
            "sub": "123",
            "preferred_username": "superuser",
            "email": "superuser@example.com",
            "realm_access": {
                "roles": ["admin", "actionnaire", "user"]
            }
        }
        
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = user_with_all_roles
            
            response = client.get("/test-require-all-roles")
            
            assert response.status_code == 200
            assert response.json()["message"] == "All roles access granted"
            assert response.json()["user"] == user_with_all_roles

    @pytest.mark.asyncio
    async def test_require_all_roles_failure(self, client, admin_user):
        """Test d'intégration pour l'endpoint require_all_roles avec échec"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user
            
            response = client.get("/test-require-all-roles")
            
            assert response.status_code == 403
            assert response.json()["detail"] == "Missing required roles: actionnaire"

    @pytest.mark.asyncio
    async def test_require_all_roles_multiple_missing(self, client, user_without_roles):
        """Test d'intégration pour l'endpoint require_all_roles avec plusieurs rôles manquants"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = user_without_roles
            
            response = client.get("/test-require-all-roles")
            
            assert response.status_code == 403
            assert response.json()["detail"] == "Missing required roles: admin, actionnaire"

    @pytest.mark.asyncio
    async def test_require_role_with_empty_realm_access(self, client):
        """Test d'intégration pour require_role avec realm_access vide"""
        user_empty_realm = {
            "sub": "123",
            "preferred_username": "user",
            "email": "user@example.com",
            "realm_access": {}
        }
        
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = user_empty_realm
            
            response = client.get("/test-require-role-admin")
            
            assert response.status_code == 403
            assert response.json()["detail"] == "Role 'admin' is required"

    @pytest.mark.asyncio
    async def test_require_role_with_none_realm_access(self, client):
        """Test d'intégration pour require_role avec realm_access None"""
        user_none_realm = {
            "sub": "123",
            "preferred_username": "user",
            "email": "user@example.com",
            "realm_access": None
        }
        
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = user_none_realm
            
            response = client.get("/test-require-role-admin")
            
            assert response.status_code == 403
            assert response.json()["detail"] == "Role 'admin' is required"
