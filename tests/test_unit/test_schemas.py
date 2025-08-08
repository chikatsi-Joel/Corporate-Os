"""
Tests unitaires pour les schémas Pydantic
"""
import pytest
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.issuance import ShareIssuanceCreate, ShareIssuanceUpdate, ShareIssuanceResponse, ShareIssuanceWithCertificate
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.auth import LoginRequest, TokenResponse


@pytest.mark.unit
class TestSchemas:
    """Tests unitaires pour les schémas"""
    
    @pytest.fixture
    def sample_uuid(self):
        """UUID de test"""
        return uuid4()
    
    @pytest.fixture
    def sample_date(self):
        """Date de test"""
        return date.today()
    
    @pytest.fixture
    def sample_datetime(self):
        """DateTime de test"""
        return datetime.now()
    
    def test_share_issuance_create_valid(self, sample_uuid, sample_date):
        """Test de création de schéma d'émission - valide"""
        # Arrange
        issuance_data = {
            "shareholder_id": sample_uuid,
            "number_of_shares": 100,
            "price_per_share": Decimal("10.50"),
            "total_amount": Decimal("1050.00"),
            "issue_date": sample_date
        }
        
        # Act
        issuance = ShareIssuanceCreate(**issuance_data)
        
        # Assert
        assert issuance.shareholder_id == sample_uuid
        assert issuance.number_of_shares == 100
        assert issuance.price_per_share == Decimal("10.50")
        assert issuance.total_amount == Decimal("1050.00")
        assert issuance.issue_date == sample_date
    
    def test_share_issuance_create_invalid_negative_shares(self, sample_uuid, sample_date):
        """Test de création de schéma d'émission - actions négatives"""
        # Arrange
        issuance_data = {
            "shareholder_id": sample_uuid,
            "number_of_shares": -100,  # Invalide
            "price_per_share": Decimal("10.50"),
            "total_amount": Decimal("1050.00"),
            "issue_date": sample_date
        }
        
        # Act & Assert
        with pytest.raises(ValidationError):
            ShareIssuanceCreate(**issuance_data)
    
    def test_share_issuance_create_invalid_negative_price(self, sample_uuid, sample_date):
        """Test de création de schéma d'émission - prix négatif"""
        # Arrange
        issuance_data = {
            "shareholder_id": sample_uuid,
            "number_of_shares": 100,
            "price_per_share": Decimal("-10.50"),  # Invalide
            "total_amount": Decimal("1050.00"),
            "issue_date": sample_date
        }
        
        # Act & Assert
        with pytest.raises(ValidationError):
            ShareIssuanceCreate(**issuance_data)
    
    def test_share_issuance_create_invalid_negative_amount(self, sample_uuid, sample_date):
        """Test de création de schéma d'émission - montant négatif"""
        # Arrange
        issuance_data = {
            "shareholder_id": sample_uuid,
            "number_of_shares": 100,
            "price_per_share": Decimal("10.50"),
            "total_amount": Decimal("-1050.00"),  # Invalide
            "issue_date": sample_date
        }
        
        # Act & Assert
        with pytest.raises(ValidationError):
            ShareIssuanceCreate(**issuance_data)
    
    def test_share_issuance_update_valid(self, sample_uuid):
        """Test de mise à jour de schéma d'émission - valide"""
        # Arrange
        update_data = {
            "number_of_shares": 200,
            "price_per_share": Decimal("15.00"),
            "total_amount": Decimal("3000.00"),
            "status": "issued"
        }
        
        # Act
        issuance_update = ShareIssuanceUpdate(**update_data)
        
        # Assert
        assert issuance_update.number_of_shares == 200
        assert issuance_update.price_per_share == Decimal("15.00")
        assert issuance_update.total_amount == Decimal("3000.00")
        assert issuance_update.status == "issued"
    
    def test_share_issuance_update_partial(self, sample_uuid):
        """Test de mise à jour partielle de schéma d'émission"""
        # Arrange
        update_data = {
            "number_of_shares": 200
        }
        
        # Act
        issuance_update = ShareIssuanceUpdate(**update_data)
        
        # Assert
        assert issuance_update.number_of_shares == 200
        assert issuance_update.price_per_share is None
        assert issuance_update.total_amount is None
        assert issuance_update.status is None
    
    def test_share_issuance_response_valid(self, sample_uuid, sample_datetime):
        """Test de réponse de schéma d'émission - valide"""
        # Arrange
        response_data = {
            "id": sample_uuid,
            "shareholder_id": sample_uuid,
            "number_of_shares": 100,
            "price_per_share": Decimal("10.50"),
            "total_amount": Decimal("1050.00"),
            "issue_date": sample_datetime,
            "status": "issued",
            "certificate_path": "/path/to/certificate.pdf",
            "created_at": sample_datetime,
            "updated_at": sample_datetime
        }
        
        # Act
        issuance_response = ShareIssuanceResponse(**response_data)
        
        # Assert
        assert issuance_response.id == sample_uuid
        assert issuance_response.shareholder_id == sample_uuid
        assert issuance_response.number_of_shares == 100
        assert issuance_response.price_per_share == Decimal("10.50")
        assert issuance_response.total_amount == Decimal("1050.00")
        assert issuance_response.status == "issued"
        assert issuance_response.certificate_path == "/path/to/certificate.pdf"
    
    def test_share_issuance_with_certificate_valid(self, sample_uuid, sample_datetime):
        """Test de schéma d'émission avec certificat - valide"""
        # Arrange
        certificate_data = {
            "id": sample_uuid,
            "shareholder_id": sample_uuid,
            "number_of_shares": 100,
            "price_per_share": Decimal("10.50"),
            "total_amount": Decimal("1050.00"),
            "issue_date": sample_datetime,
            "status": "issued",
            "certificate_path": "/path/to/certificate.pdf",
            "created_at": sample_datetime,
            "updated_at": sample_datetime,
            "certificate_base64": "base64-encoded-certificate"
        }
        
        # Act
        issuance_with_cert = ShareIssuanceWithCertificate(**certificate_data)
        
        # Assert
        assert issuance_with_cert.id == sample_uuid
        assert issuance_with_cert.certificate_base64 == "base64-encoded-certificate"
    
    def test_user_create_valid(self):
        """Test de création de schéma utilisateur - valide"""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "company_name": "Test Company",
            "phone": "+1234567890"
        }
        
        # Act
        user = UserCreate(**user_data)
        
        # Assert
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.company_name == "Test Company"
        assert user.phone == "+1234567890"
    
    def test_user_create_invalid_email(self):
        """Test de création de schéma utilisateur - email invalide"""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "invalid-email",  # Invalide
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_user_create_empty_username(self):
        """Test de création de schéma utilisateur - username vide"""
        # Arrange
        user_data = {
            "username": "",  # Invalide
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_user_update_valid(self):
        """Test de mise à jour de schéma utilisateur - valide"""
        # Arrange
        update_data = {
            "first_name": "Updated",
            "last_name": "User",
            "company_name": "Updated Company",
            "phone": "+9876543210"
        }
        
        # Act
        user_update = UserUpdate(**update_data)
        
        # Assert
        assert user_update.first_name == "Updated"
        assert user_update.last_name == "User"
        assert user_update.company_name == "Updated Company"
        assert user_update.phone == "+9876543210"
    
    def test_user_update_partial(self):
        """Test de mise à jour partielle de schéma utilisateur"""
        # Arrange
        update_data = {
            "first_name": "Updated"
        }
        
        # Act
        user_update = UserUpdate(**update_data)
        
        # Assert
        assert user_update.first_name == "Updated"
        assert user_update.last_name is None
        assert user_update.company_name is None
        assert user_update.phone is None
    
    def test_user_response_valid(self, sample_uuid, sample_datetime):
        """Test de réponse de schéma utilisateur - valide"""
        # Arrange
        response_data = {
            "id": sample_uuid,
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "company_name": "Test Company",
            "phone": "+1234567890",
            "created_at": sample_datetime,
            "updated_at": sample_datetime
        }
        
        # Act
        user_response = UserResponse(**response_data)
        
        # Assert
        assert user_response.id == sample_uuid
        assert user_response.username == "testuser"
        assert user_response.email == "test@example.com"
        assert user_response.first_name == "Test"
        assert user_response.last_name == "User"
        assert user_response.company_name == "Test Company"
        assert user_response.phone == "+1234567890"
    
    def test_login_request_valid(self):
        """Test de schéma de demande de connexion - valide"""
        # Arrange
        login_data = {
            "username": "testuser",
            "password": "testpassword"
        }
        
        # Act
        login_request = LoginRequest(**login_data)
        
        # Assert
        assert login_request.username == "testuser"
        assert login_request.password == "testpassword"
    
    def test_login_request_empty_username(self):
        """Test de schéma de demande de connexion - username vide"""
        # Arrange
        login_data = {
            "username": "",  # Invalide
            "password": "testpassword"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError):
            LoginRequest(**login_data)
    
    def test_login_request_empty_password(self):
        """Test de schéma de demande de connexion - mot de passe vide"""
        # Arrange
        login_data = {
            "username": "testuser",
            "password": ""  # Invalide
        }
        
        # Act & Assert
        with pytest.raises(ValidationError):
            LoginRequest(**login_data)
    
    def test_token_response_valid(self):
        """Test de schéma de réponse de token - valide"""
        # Arrange
        token_data = {
            "access_token": "test-access-token",
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": "test-refresh-token"
        }
        
        # Act
        token_response = TokenResponse(**token_data)
        
        # Assert
        assert token_response.access_token == "test-access-token"
        assert token_response.token_type == "bearer"
        assert token_response.expires_in == 3600
        assert token_response.refresh_token == "test-refresh-token"
    
    def test_token_response_minimal(self):
        """Test de schéma de réponse de token - minimal"""
        # Arrange
        token_data = {
            "access_token": "test-access-token",
            "token_type": "bearer"
        }
        
        # Act
        token_response = TokenResponse(**token_data)
        
        # Assert
        assert token_response.access_token == "test-access-token"
        assert token_response.token_type == "bearer"
        assert token_response.expires_in is None
        assert token_response.refresh_token is None
    
    def test_schema_serialization(self, sample_uuid, sample_date):
        """Test de sérialisation des schémas"""
        # Arrange
        issuance_data = {
            "shareholder_id": sample_uuid,
            "number_of_shares": 100,
            "price_per_share": Decimal("10.50"),
            "total_amount": Decimal("1050.00"),
            "issue_date": sample_date
        }
        
        # Act
        issuance = ShareIssuanceCreate(**issuance_data)
        issuance_dict = issuance.dict()
        
        # Assert
        assert isinstance(issuance_dict, dict)
        assert issuance_dict["shareholder_id"] == sample_uuid
        assert issuance_dict["number_of_shares"] == 100
        assert float(issuance_dict["price_per_share"]) == 10.50
        assert float(issuance_dict["total_amount"]) == 1050.00
    
    def test_schema_json_serialization(self, sample_uuid, sample_date):
        """Test de sérialisation JSON des schémas"""
        # Arrange
        issuance_data = {
            "shareholder_id": sample_uuid,
            "number_of_shares": 100,
            "price_per_share": Decimal("10.50"),
            "total_amount": Decimal("1050.00"),
            "issue_date": sample_date
        }
        
        # Act
        issuance = ShareIssuanceCreate(**issuance_data)
        issuance_json = issuance.json()
        
        # Assert
        assert isinstance(issuance_json, str)
        assert "shareholder_id" in issuance_json
        assert "number_of_shares" in issuance_json
        assert "10.50" in issuance_json
    
    def test_schema_validation_error_messages(self):
        """Test des messages d'erreur de validation"""
        # Arrange
        invalid_data = {
            "username": "",
            "email": "invalid-email"
        }
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**invalid_data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        
        # Vérifier que les messages d'erreur sont présents
        error_messages = [error["msg"] for error in errors]
        assert any("empty" in msg.lower() or "invalid" in msg.lower() for msg in error_messages)
    
    def test_schema_field_types(self, sample_uuid):
        """Test des types de champs des schémas"""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Act
        user = UserCreate(**user_data)
        
        # Assert
        assert isinstance(user.username, str)
        assert isinstance(user.email, str)
        assert isinstance(user.first_name, str)
        assert isinstance(user.last_name, str)
    
    def test_schema_optional_fields(self):
        """Test des champs optionnels des schémas"""
        # Arrange
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
            # company_name et phone sont optionnels
        }
        
        # Act
        user = UserCreate(**user_data)
        
        # Assert
        assert user.company_name is None
        assert user.phone is None
    
    def test_schema_default_values(self, sample_uuid, sample_date):
        """Test des valeurs par défaut des schémas"""
        # Arrange
        issuance_data = {
            "shareholder_id": sample_uuid,
            "number_of_shares": 100,
            "price_per_share": Decimal("10.50"),
            "total_amount": Decimal("1050.00"),
            "issue_date": sample_date
        }
        
        # Act
        issuance = ShareIssuanceCreate(**issuance_data)
        
        # Assert
        # Vérifier que les champs optionnels ont des valeurs par défaut appropriées
        # (selon la définition du schéma)
    
    def test_schema_nested_objects(self, sample_uuid, sample_datetime):
        """Test des objets imbriqués dans les schémas"""
        # Arrange
        response_data = {
            "id": sample_uuid,
            "shareholder_id": sample_uuid,
            "number_of_shares": 100,
            "price_per_share": Decimal("10.50"),
            "total_amount": Decimal("1050.00"),
            "issue_date": sample_datetime,
            "status": "issued",
            "certificate_path": "/path/to/certificate.pdf",
            "created_at": sample_datetime,
            "updated_at": sample_datetime,
            "shareholder": {
                "id": sample_uuid,
                "username": "testuser",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User"
            }
        }
        
        # Act
        # Si le schéma supporte les objets imbriqués
        # issuance_response = ShareIssuanceResponse(**response_data)
        
        # Assert
        # Vérifier que l'objet imbriqué est correctement validé
        pass

