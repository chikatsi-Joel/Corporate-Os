import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, Request
from app.core.check_role import (
    get_current_user,
    require_role,
    require_any_role,
    require_all_roles
)


class TestCheckRole:
    """Tests unitaires pour les fonctions de vérification des rôles"""

    @pytest.fixture
    def mock_request(self):
        """Fixture pour créer un objet Request mocké"""
        request = MagicMock(spec=Request)
        return request

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
    async def test_get_current_user_success(self, mock_request, admin_user):
        """Test de récupération réussie d'un utilisateur"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user
            
            result = await get_current_user(mock_request)
            
            assert result == admin_user
            mock_get_user.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_get_current_user_no_user(self, mock_request):
        """Test de récupération d'utilisateur quand aucun utilisateur n'est trouvé"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "User not authenticated"

    @pytest.mark.asyncio
    async def test_get_current_user_exception(self, mock_request):
        """Test de récupération d'utilisateur avec une exception"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.side_effect = Exception("Test exception")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "User not authenticated"

    @pytest.mark.asyncio
    async def test_require_role_success(self, mock_request, admin_user):
        """Test de vérification de rôle réussie"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user
            
            role_dependency = require_role("admin")
            result = await role_dependency(mock_request)
            
            assert result == admin_user

    @pytest.mark.asyncio
    async def test_require_role_failure(self, mock_request, actionnaire_user):
        """Test de vérification de rôle échouée"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = actionnaire_user
            
            role_dependency = require_role("admin")
            
            with pytest.raises(HTTPException) as exc_info:
                await role_dependency(mock_request)
            
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "Role 'admin' is required"

    @pytest.mark.asyncio
    async def test_require_role_no_roles(self, mock_request, user_without_roles):
        """Test de vérification de rôle avec un utilisateur sans rôles"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = user_without_roles
            
            role_dependency = require_role("admin")
            
            with pytest.raises(HTTPException) as exc_info:
                await role_dependency(mock_request)
            
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "Role 'admin' is required"

    @pytest.mark.asyncio
    async def test_require_any_role_success_first_role(self, mock_request, admin_user):
        """Test de vérification de rôles multiples réussie avec le premier rôle"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user
            
            role_dependency = require_any_role(["admin", "actionnaire"])
            result = await role_dependency(mock_request)
            
            assert result == admin_user

    @pytest.mark.asyncio
    async def test_require_any_role_success_second_role(self, mock_request, actionnaire_user):
        """Test de vérification de rôles multiples réussie avec le deuxième rôle"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = actionnaire_user
            
            role_dependency = require_any_role(["admin", "actionnaire"])
            result = await role_dependency(mock_request)
            
            assert result == actionnaire_user

    @pytest.mark.asyncio
    async def test_require_any_role_failure(self, mock_request, user_without_roles):
        """Test de vérification de rôles multiples échouée"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = user_without_roles
            
            role_dependency = require_any_role(["admin", "actionnaire"])
            
            with pytest.raises(HTTPException) as exc_info:
                await role_dependency(mock_request)
            
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "One of these roles is required: admin, actionnaire"

    @pytest.mark.asyncio
    async def test_require_all_roles_success(self, mock_request):
        """Test de vérification de tous les rôles réussie"""
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
            
            role_dependency = require_all_roles(["admin", "actionnaire"])
            result = await role_dependency(mock_request)
            
            assert result == user_with_all_roles

    @pytest.mark.asyncio
    async def test_require_all_roles_failure(self, mock_request, admin_user):
        """Test de vérification de tous les rôles échouée"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user
            
            role_dependency = require_all_roles(["admin", "actionnaire"])
            
            with pytest.raises(HTTPException) as exc_info:
                await role_dependency(mock_request)
            
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "Missing required roles: actionnaire"

    @pytest.mark.asyncio
    async def test_require_all_roles_multiple_missing(self, mock_request, user_without_roles):
        """Test de vérification de tous les rôles avec plusieurs rôles manquants"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = user_without_roles
            
            role_dependency = require_all_roles(["admin", "actionnaire", "user"])
            
            with pytest.raises(HTTPException) as exc_info:
                await role_dependency(mock_request)
            
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "Missing required roles: admin, actionnaire, user"

    @pytest.mark.asyncio
    async def test_require_role_with_empty_realm_access(self, mock_request):
        """Test de vérification de rôle avec realm_access vide"""
        user_empty_realm = {
            "sub": "123",
            "preferred_username": "user",
            "email": "user@example.com",
            "realm_access": {}
        }
        
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = user_empty_realm
            
            role_dependency = require_role("admin")
            
            with pytest.raises(HTTPException) as exc_info:
                await role_dependency(mock_request)
            
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "Role 'admin' is required"

    @pytest.mark.asyncio
    async def test_require_role_with_none_realm_access(self, mock_request):
        """Test de vérification de rôle avec realm_access None"""
        user_none_realm = {
            "sub": "123",
            "preferred_username": "user",
            "email": "user@example.com",
            "realm_access": None
        }
        
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = user_none_realm
            
            role_dependency = require_role("admin")
            
            with pytest.raises(HTTPException) as exc_info:
                await role_dependency(mock_request)
            
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "Role 'admin' is required"

    @pytest.mark.asyncio
    async def test_require_any_role_with_empty_list(self, mock_request, admin_user):
        """Test de vérification de rôles avec une liste vide"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user
            
            role_dependency = require_any_role([])
            
            with pytest.raises(HTTPException) as exc_info:
                await role_dependency(mock_request)
            
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "One of these roles is required: "

    @pytest.mark.asyncio
    async def test_require_all_roles_with_empty_list(self, mock_request, admin_user):
        """Test de vérification de tous les rôles avec une liste vide"""
        with patch('app.core.check_role.get_user', new_callable=AsyncMock) as mock_get_user:
            mock_get_user.return_value = admin_user
            
            role_dependency = require_all_roles([])
            result = await role_dependency(mock_request)
            
            # Si la liste est vide, tous les rôles requis sont présents (aucun requis)
            assert result == admin_user
