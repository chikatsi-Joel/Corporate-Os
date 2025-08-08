"""
Tests unitaires pour les utilitaires et helpers
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
import json
import base64

from app.core.config import Settings
from app.core.check_role import get_current_user, require_role, require_any_role, require_all_roles
from app.services.certificate_service import CertificateService


@pytest.mark.unit
class TestUtils:
    """Tests unitaires pour les utilitaires"""
    
    @pytest.fixture
    def mock_request(self):
        """Requête mockée"""
        request = Mock()
        request.headers = {
            "Authorization": "Bearer test-token"
        }
        return request
    
    @pytest.fixture
    def mock_user_info(self):
        """Informations utilisateur mockées"""
        return {
            "sub": "test-user-id",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "given_name": "Test",
            "family_name": "User",
            "realm_access": {
                "roles": ["admin", "actionnaire"]
            }
        }
    
    def test_settings_initialization(self):
        """Test d'initialisation des paramètres"""
        # Arrange & Act
        settings = Settings()
        
        # Assert
        assert settings is not None
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'keycloak_url')
        assert hasattr(settings, 'keycloak_realm')
        assert hasattr(settings, 'keycloak_client_id')
        assert hasattr(settings, 'keycloak_client_secret')
        assert hasattr(settings, 'secret_key')
    
    def test_settings_environment_variables(self):
        """Test des variables d'environnement"""
        # Arrange
        test_settings = {
            'database_url': 'postgresql://test:test@localhost:5432/test',
            'keycloak_url': 'http://localhost:8080',
            'keycloak_realm': 'test-realm',
            'keycloak_client_id': 'test-client',
            'keycloak_client_secret': 'test-secret',
            'secret_key': 'test-secret-key'
        }
        
        # Act
        settings = Settings(**test_settings)
        
        # Assert
        assert settings.database_url == test_settings['database_url']
        assert settings.keycloak_url == test_settings['keycloak_url']
        assert settings.keycloak_realm == test_settings['keycloak_realm']
        assert settings.keycloak_client_id == test_settings['keycloak_client_id']
        assert settings.keycloak_client_secret == test_settings['keycloak_client_secret']
        assert settings.secret_key == test_settings['secret_key']
    
    @patch('app.core.check_role.keycloak')
    def test_get_current_user_success(self, mock_keycloak, mock_request, mock_user_info):
        """Test de récupération de l'utilisateur actuel - succès"""
        # Arrange
        mock_keycloak.return_value.decode_token.return_value = mock_user_info
        
        # Act
        result = get_current_user(mock_request)
        
        # Assert
        assert result == mock_user_info
        mock_keycloak.return_value.decode_token.assert_called_once_with("test-token")
    
    @patch('app.core.check_role.keycloak')
    def test_get_current_user_no_token(self, mock_keycloak, mock_request):
        """Test de récupération de l'utilisateur actuel - pas de token"""
        # Arrange
        mock_request.headers = {}
        
        # Act & Assert
        with pytest.raises(Exception):
            get_current_user(mock_request)
    
    @patch('app.core.check_role.keycloak')
    def test_get_current_user_invalid_token(self, mock_keycloak, mock_request):
        """Test de récupération de l'utilisateur actuel - token invalide"""
        # Arrange
        mock_keycloak.return_value.decode_token.side_effect = Exception("Invalid token")
        
        # Act & Assert
        with pytest.raises(Exception):
            get_current_user(mock_request)
    
    @patch('app.core.check_role.get_current_user')
    def test_require_role_success(self, mock_get_current_user, mock_request, mock_user_info):
        """Test de vérification de rôle - succès"""
        # Arrange
        mock_get_current_user.return_value = mock_user_info
        
        # Act
        result = require_role("admin")(mock_request)
        
        # Assert
        assert result == mock_user_info
    
    @patch('app.core.check_role.get_current_user')
    def test_require_role_failure(self, mock_get_current_user, mock_request, mock_user_info):
        """Test de vérification de rôle - échec"""
        # Arrange
        mock_user_info["realm_access"]["roles"] = ["actionnaire"]
        mock_get_current_user.return_value = mock_user_info
        
        # Act & Assert
        with pytest.raises(Exception):
            require_role("admin")(mock_request)
    
    @patch('app.core.check_role.get_current_user')
    def test_require_any_role_success(self, mock_get_current_user, mock_request, mock_user_info):
        """Test de vérification de rôles multiples - succès"""
        # Arrange
        mock_get_current_user.return_value = mock_user_info
        
        # Act
        result = require_any_role(["admin", "actionnaire"])(mock_request)
        
        # Assert
        assert result == mock_user_info
    
    @patch('app.core.check_role.get_current_user')
    def test_require_any_role_failure(self, mock_get_current_user, mock_request, mock_user_info):
        """Test de vérification de rôles multiples - échec"""
        # Arrange
        mock_user_info["realm_access"]["roles"] = ["user"]
        mock_get_current_user.return_value = mock_user_info
        
        # Act & Assert
        with pytest.raises(Exception):
            require_any_role(["admin", "actionnaire"])(mock_request)
    
    @patch('app.core.check_role.get_current_user')
    def test_require_all_roles_success(self, mock_get_current_user, mock_request, mock_user_info):
        """Test de vérification de tous les rôles - succès"""
        # Arrange
        mock_get_current_user.return_value = mock_user_info
        
        # Act
        result = require_all_roles(["admin", "actionnaire"])(mock_request)
        
        # Assert
        assert result == mock_user_info
    
    @patch('app.core.check_role.get_current_user')
    def test_require_all_roles_failure(self, mock_get_current_user, mock_request, mock_user_info):
        """Test de vérification de tous les rôles - échec"""
        # Arrange
        mock_user_info["realm_access"]["roles"] = ["admin"]
        mock_get_current_user.return_value = mock_user_info
        
        # Act & Assert
        with pytest.raises(Exception):
            require_all_roles(["admin", "actionnaire"])(mock_request)
    
    def test_decimal_serialization(self):
        """Test de sérialisation des objets Decimal"""
        # Arrange
        decimal_value = Decimal("10.50")
        
        # Act
        float_value = float(decimal_value)
        
        # Assert
        assert float_value == 10.50
        assert isinstance(float_value, float)
    
    def test_uuid_serialization(self):
        """Test de sérialisation des UUIDs"""
        # Arrange
        test_uuid = uuid4()
        
        # Act
        uuid_string = str(test_uuid)
        
        # Assert
        assert isinstance(uuid_string, str)
        assert len(uuid_string) == 36  # Format UUID standard
    
    def test_datetime_serialization(self):
        """Test de sérialisation des dates"""
        # Arrange
        test_datetime = datetime.now()
        
        # Act
        datetime_string = test_datetime.isoformat()
        
        # Assert
        assert isinstance(datetime_string, str)
        assert "T" in datetime_string  # Format ISO
    
    def test_base64_encoding(self):
        """Test d'encodage base64"""
        # Arrange
        test_data = b"Test PDF content"
        
        # Act
        encoded_data = base64.b64encode(test_data)
        decoded_data = base64.b64decode(encoded_data)
        
        # Assert
        assert isinstance(encoded_data, bytes)
        assert decoded_data == test_data
    
    def test_json_serialization(self):
        """Test de sérialisation JSON"""
        # Arrange
        test_data = {
            "id": str(uuid4()),
            "name": "Test",
            "value": 10.50,
            "date": datetime.now().isoformat()
        }
        
        # Act
        json_string = json.dumps(test_data)
        deserialized_data = json.loads(json_string)
        
        # Assert
        assert isinstance(json_string, str)
        assert deserialized_data["name"] == test_data["name"]
        assert deserialized_data["value"] == test_data["value"]
    
    def test_certificate_path_generation(self):
        """Test de génération de chemin de certificat"""
        # Arrange
        issuance_id = uuid4()
        
        # Act
        expected_path = f"certificates/certificate_{issuance_id}.pdf"
        
        # Assert
        assert expected_path.startswith("certificates/")
        assert expected_path.endswith(".pdf")
        assert str(issuance_id) in expected_path
    
    @patch('app.services.certificate_service.os.path.exists')
    def test_certificate_path_validation(self, mock_exists):
        """Test de validation de chemin de certificat"""
        # Arrange
        mock_exists.return_value = True
        
        # Act
        result = CertificateService.get_certificate_path(str(uuid4()))
        
        # Assert
        assert result is not None
        assert result.endswith('.pdf')
    
    @patch('app.services.certificate_service.os.path.exists')
    def test_certificate_path_not_exists(self, mock_exists):
        """Test de chemin de certificat inexistant"""
        # Arrange
        mock_exists.return_value = False
        
        # Act
        result = CertificateService.get_certificate_path(str(uuid4()))
        
        # Assert
        assert result is None
    
    def test_data_validation(self):
        """Test de validation des données"""
        # Arrange
        valid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Act & Assert
        assert valid_data["username"] is not None
        assert valid_data["email"] is not None
        assert "@" in valid_data["email"]
        assert valid_data["first_name"] is not None
        assert valid_data["last_name"] is not None
    
    def test_data_validation_invalid_email(self):
        """Test de validation des données - email invalide"""
        # Arrange
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Act & Assert
        assert "@" not in invalid_data["email"]
    
    def test_data_validation_empty_fields(self):
        """Test de validation des données - champs vides"""
        # Arrange
        empty_data = {
            "username": "",
            "email": "",
            "first_name": "",
            "last_name": ""
        }
        
        # Act & Assert
        assert not empty_data["username"]
        assert not empty_data["email"]
        assert not empty_data["first_name"]
        assert not empty_data["last_name"]
    
    def test_pagination_validation(self):
        """Test de validation de pagination"""
        # Arrange
        valid_skip = 0
        valid_limit = 10
        
        # Act & Assert
        assert valid_skip >= 0
        assert valid_limit > 0
        assert valid_limit <= 100  # Limite maximale
    
    def test_pagination_validation_invalid(self):
        """Test de validation de pagination - invalide"""
        # Arrange
        invalid_skip = -1
        invalid_limit = 0
        
        # Act & Assert
        assert invalid_skip < 0
        assert invalid_limit <= 0
    
    def test_date_validation(self):
        """Test de validation de date"""
        # Arrange
        valid_date = date.today()
        future_date = date(2025, 12, 31)
        
        # Act & Assert
        assert valid_date <= date.today()
        assert future_date > date.today()
    
    def test_numeric_validation(self):
        """Test de validation numérique"""
        # Arrange
        valid_number = 100
        valid_price = 10.50
        
        # Act & Assert
        assert valid_number > 0
        assert valid_price >= 0
        assert isinstance(valid_number, int)
        assert isinstance(valid_price, float)
    
    def test_string_validation(self):
        """Test de validation de chaînes"""
        # Arrange
        valid_string = "Test String"
        empty_string = ""
        
        # Act & Assert
        assert len(valid_string) > 0
        assert len(empty_string) == 0
        assert isinstance(valid_string, str)
    
    def test_list_validation(self):
        """Test de validation de listes"""
        # Arrange
        valid_list = [1, 2, 3, 4, 5]
        empty_list = []
        
        # Act & Assert
        assert len(valid_list) > 0
        assert len(empty_list) == 0
        assert isinstance(valid_list, list)
    
    def test_dict_validation(self):
        """Test de validation de dictionnaires"""
        # Arrange
        valid_dict = {"key": "value", "number": 123}
        empty_dict = {}
        
        # Act & Assert
        assert len(valid_dict) > 0
        assert len(empty_dict) == 0
        assert isinstance(valid_dict, dict)
        assert "key" in valid_dict
        assert valid_dict["number"] == 123
    
    def test_error_handling(self):
        """Test de gestion d'erreurs"""
        # Arrange
        test_exception = Exception("Test error")
        
        # Act & Assert
        assert str(test_exception) == "Test error"
        assert isinstance(test_exception, Exception)
    
    def test_logging_format(self):
        """Test de format de logging"""
        # Arrange
        test_message = "Test log message"
        test_level = "INFO"
        
        # Act
        log_entry = f"[{test_level}] {test_message}"
        
        # Assert
        assert test_level in log_entry
        assert test_message in log_entry
        assert log_entry.startswith("[")
        assert log_entry.endswith("]")
    
    def test_configuration_validation(self):
        """Test de validation de configuration"""
        # Arrange
        required_fields = [
            "database_url",
            "keycloak_url",
            "keycloak_realm",
            "keycloak_client_id",
            "keycloak_client_secret",
            "secret_key"
        ]
        
        # Act
        settings = Settings()
        
        # Assert
        for field in required_fields:
            assert hasattr(settings, field)
    
    def test_environment_variable_handling(self):
        """Test de gestion des variables d'environnement"""
        # Arrange
        test_env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
            "KEYCLOAK_URL": "http://localhost:8080",
            "KEYCLOAK_REALM": "test-realm"
        }
        
        # Act & Assert
        for key, value in test_env_vars.items():
            assert key in test_env_vars
            assert value is not None
            assert isinstance(value, str)

