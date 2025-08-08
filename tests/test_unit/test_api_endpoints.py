"""
Tests unitaires pour les endpoints API
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.database.models import ShareholderProfile, ShareIssuance
from app.schemas.issuance import ShareIssuanceCreate
from app.schemas.user import UserCreate


@pytest.mark.unit
class TestAPIEndpoints:
    """Tests unitaires pour les endpoints API"""
    
    @pytest.fixture
    def client(self):
        """Client de test FastAPI"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Session de base de données mockée"""
        return Mock()
    
    @pytest.fixture
    def sample_shareholder(self):
        """Actionnaire de test"""
        return ShareholderProfile(
            id=uuid4(),
            keycloak_id="test-keycloak-id",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            company_name="Test Company",
            phone="+1234567890",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_issuance(self, sample_shareholder):
        """Émission de test"""
        return ShareIssuance(
            id=uuid4(),
            shareholder_id=sample_shareholder.id,
            number_of_shares=100,
            price_per_share=Decimal("10.50"),
            total_amount=Decimal("1050.00"),
            issue_date=datetime.now(),
            status="issued",
            certificate_path="/path/to/certificate.pdf",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def auth_headers(self):
        """Headers d'authentification"""
        return {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json"
        }
    
    @patch('app.api.shareholders.get_db')
    def test_get_shareholders_success(self, mock_get_db, client, mock_db_session, sample_shareholder, auth_headers):
        """Test de récupération des actionnaires - succès"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [sample_shareholder]
        
        # Act
        response = client.get("/api/shareholders/", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == sample_shareholder.username
        assert data[0]["email"] == sample_shareholder.email
    
    @patch('app.api.shareholders.get_db')
    def test_get_shareholders_unauthorized(self, mock_get_db, client):
        """Test de récupération des actionnaires - non autorisé"""
        # Arrange
        mock_get_db.return_value = Mock()
        
        # Act
        response = client.get("/api/shareholders/")
        
        # Assert
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    @patch('app.api.shareholders.get_db')
    def test_create_shareholder_success(self, mock_get_db, client, mock_db_session, auth_headers):
        """Test de création d'actionnaire - succès"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        shareholder_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "company_name": "New Company",
            "phone": "+9876543210"
        }
        
        # Mock de l'objet créé
        mock_shareholder = Mock(spec=ShareholderProfile)
        mock_shareholder.id = uuid4()
        mock_shareholder.username = shareholder_data["username"]
        mock_shareholder.email = shareholder_data["email"]
        mock_shareholder.first_name = shareholder_data["first_name"]
        mock_shareholder.last_name = shareholder_data["last_name"]
        mock_shareholder.company_name = shareholder_data["company_name"]
        mock_shareholder.phone = shareholder_data["phone"]
        
        with patch('app.api.shareholders.ShareholderProfile') as mock_shareholder_class:
            mock_shareholder_class.return_value = mock_shareholder
            
            # Act
            response = client.post("/api/shareholders/", json=shareholder_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == shareholder_data["username"]
        assert data["email"] == shareholder_data["email"]
    
    @patch('app.api.shareholders.get_db')
    def test_create_shareholder_duplicate_username(self, mock_get_db, client, mock_db_session, auth_headers):
        """Test de création d'actionnaire - username en double"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = Mock()
        
        shareholder_data = {
            "username": "existinguser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User"
        }
        
        # Act
        response = client.post("/api/shareholders/", json=shareholder_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('app.api.shareholders.get_db')
    def test_get_shareholder_by_id_success(self, mock_get_db, client, mock_db_session, sample_shareholder, auth_headers):
        """Test de récupération d'actionnaire par ID - succès"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Act
        response = client.get(f"/api/shareholders/{sample_shareholder.id}", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_shareholder.id)
        assert data["username"] == sample_shareholder.username
        assert data["email"] == sample_shareholder.email
    
    @patch('app.api.shareholders.get_db')
    def test_get_shareholder_by_id_not_found(self, mock_get_db, client, mock_db_session, auth_headers):
        """Test de récupération d'actionnaire par ID - non trouvé"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        response = client.get(f"/api/shareholders/{uuid4()}", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('app.api.issuances.get_db')
    def test_get_issuances_success(self, mock_get_db, client, mock_db_session, sample_issuance, sample_shareholder, auth_headers):
        """Test de récupération des émissions - succès"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.join.return_value.offset.return_value.limit.return_value.all.return_value = [
            (sample_issuance, sample_shareholder)
        ]
        
        # Act
        response = client.get("/api/issuances/", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(sample_issuance.id)
        assert data[0]["shareholder_id"] == str(sample_shareholder.id)
    
    @patch('app.api.issuances.get_db')
    def test_get_issuances_unauthorized(self, mock_get_db, client):
        """Test de récupération des émissions - non autorisé"""
        # Arrange
        mock_get_db.return_value = Mock()
        
        # Act
        response = client.get("/api/issuances/")
        
        # Assert
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
    
    @patch('app.api.issuances.get_db')
    @patch('app.api.issuances.IssuanceService.create_issuance')
    def test_create_issuance_success(self, mock_create_issuance, mock_get_db, client, mock_db_session, sample_shareholder, auth_headers):
        """Test de création d'émission - succès"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_create_issuance.return_value = {
            "id": str(uuid4()),
            "shareholder_id": str(sample_shareholder.id),
            "shares_count": 100,
            "share_price": 10.50,
            "total_amount": 1050.00,
            "certificate_path": "/path/to/certificate.pdf"
        }
        
        issuance_data = {
            "shareholder_id": str(sample_shareholder.id),
            "number_of_shares": 100,
            "price_per_share": 10.50,
            "total_amount": 1050.00,
            "issue_date": date.today().isoformat()
        }
        
        # Act
        response = client.post("/api/issuances/", json=issuance_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["shareholder_id"] == str(sample_shareholder.id)
        assert data["shares_count"] == 100
        assert data["share_price"] == 10.50
    
    @patch('app.api.issuances.get_db')
    def test_create_issuance_invalid_data(self, mock_get_db, client, mock_db_session, auth_headers):
        """Test de création d'émission - données invalides"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        
        invalid_issuance_data = {
            "shareholder_id": str(uuid4()),
            "number_of_shares": -100,  # Invalide
            "price_per_share": -10.50,  # Invalide
            "total_amount": -1050.00,  # Invalide
            "issue_date": date.today().isoformat()
        }
        
        # Act
        response = client.post("/api/issuances/", json=invalid_issuance_data, headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.api.issuances.get_db')
    def test_get_issuance_by_id_success(self, mock_get_db, client, mock_db_session, sample_issuance, sample_shareholder, auth_headers):
        """Test de récupération d'émission par ID - succès"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.join.return_value.filter.return_value.first.return_value = (sample_issuance, sample_shareholder)
        
        # Act
        response = client.get(f"/api/issuances/{sample_issuance.id}", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_issuance.id)
        assert data["shareholder_id"] == str(sample_shareholder.id)
        assert data["shares_count"] == 100
    
    @patch('app.api.issuances.get_db')
    def test_get_issuance_by_id_not_found(self, mock_get_db, client, mock_db_session, auth_headers):
        """Test de récupération d'émission par ID - non trouvé"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.join.return_value.filter.return_value.first.return_value = None
        
        # Act
        response = client.get(f"/api/issuances/{uuid4()}", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('app.api.issuances.get_db')
    def test_download_certificate_success(self, mock_get_db, client, mock_db_session, sample_issuance, auth_headers):
        """Test de téléchargement de certificat - succès"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_issuance
        
        # Mock du fichier
        with patch('builtins.open', mock_open(read_data=b'PDF content')):
            with patch('os.path.exists', return_value=True):
                # Act
                response = client.get(f"/api/issuances/{sample_issuance.id}/certificate", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/pdf"
    
    @patch('app.api.issuances.get_db')
    def test_download_certificate_not_found(self, mock_get_db, client, mock_db_session, auth_headers):
        """Test de téléchargement de certificat - non trouvé"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        response = client.get(f"/api/issuances/{uuid4()}/certificate", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('app.api.issuances.get_db')
    def test_get_cap_table_summary_success(self, mock_get_db, client, mock_db_session, sample_shareholder, sample_issuance, auth_headers):
        """Test de récupération du résumé de la cap table - succès"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.all.return_value = [sample_shareholder]
        mock_db_session.query.return_value.filter.return_value.all.return_value = [sample_issuance]
        
        # Act
        response = client.get("/api/issuances/cap-table/summary", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_shares" in data
        assert "total_value" in data
        assert "total_shareholders" in data
    
    @patch('app.api.auth.get_db')
    def test_login_success(self, mock_get_db, client, mock_db_session):
        """Test de connexion - succès"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        
        login_data = {
            "username": "testuser",
            "password": "testpassword"
        }
        
        # Mock de l'authentification Keycloak
        with patch('app.api.auth.keycloak') as mock_keycloak:
            mock_keycloak.return_value.token.return_value = {
                "access_token": "test-access-token",
                "refresh_token": "test-refresh-token",
                "expires_in": 3600
            }
            
            # Act
            response = client.post("/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
    
    @patch('app.api.auth.get_db')
    def test_login_invalid_credentials(self, mock_get_db, client, mock_db_session):
        """Test de connexion - identifiants invalides"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        
        login_data = {
            "username": "invaliduser",
            "password": "invalidpassword"
        }
        
        # Mock de l'authentification Keycloak échouée
        with patch('app.api.auth.keycloak') as mock_keycloak:
            mock_keycloak.return_value.token.side_effect = Exception("Invalid credentials")
            
            # Act
            response = client.post("/auth/login", data=login_data)
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_health_check_success(self, client):
        """Test de l'endpoint de santé - succès"""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_root_endpoint_success(self, client):
        """Test de l'endpoint racine - succès"""
        # Act
        response = client.get("/")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
    
    @patch('app.api.shareholders.get_db')
    def test_get_shareholder_summary_success(self, mock_get_db, client, mock_db_session, sample_shareholder, sample_issuance, auth_headers):
        """Test de récupération du résumé d'actionnaire - succès"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        mock_db_session.query.return_value.filter.return_value.all.return_value = [sample_issuance]
        
        # Act
        response = client.get(f"/api/shareholders/{sample_shareholder.id}/summary", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["shareholder_id"] == str(sample_shareholder.id)
        assert "total_shares" in data
        assert "total_value" in data
    
    @patch('app.api.shareholders.get_db')
    def test_get_shareholder_summary_not_found(self, mock_get_db, client, mock_db_session, auth_headers):
        """Test de récupération du résumé d'actionnaire - non trouvé"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        response = client.get(f"/api/shareholders/{uuid4()}/summary", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('app.api.issuances.get_db')
    def test_get_issuance_certificate_base64_success(self, mock_get_db, client, mock_db_session, sample_issuance, auth_headers):
        """Test de récupération du certificat en base64 - succès"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_issuance
        
        # Mock du fichier
        with patch('builtins.open', mock_open(read_data=b'PDF content')):
            with patch('os.path.exists', return_value=True):
                # Act
                response = client.get(f"/api/issuances/{sample_issuance.id}/certificate/base64", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "certificate_base64" in data
        assert isinstance(data["certificate_base64"], str)
    
    @patch('app.api.issuances.get_db')
    def test_get_issuance_certificate_base64_not_found(self, mock_get_db, client, mock_db_session, auth_headers):
        """Test de récupération du certificat en base64 - non trouvé"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        response = client.get(f"/api/issuances/{uuid4()}/certificate/base64", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_cors_headers(self, client):
        """Test des headers CORS"""
        # Act
        response = client.options("/health", headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        })
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        # Vérifier que les headers CORS sont présents
        cors_headers = response.headers.get("Access-Control-Allow-Origin")
        if cors_headers:
            assert cors_headers != "*"  # Ne doit pas être trop permissif
    
    def test_error_handling_404(self, client):
        """Test de gestion d'erreur 404"""
        # Act
        response = client.get("/api/nonexistent")
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
    
    def test_error_handling_422(self, client):
        """Test de gestion d'erreur 422 (validation)"""
        # Arrange
        invalid_data = {
            "invalid_field": "invalid_value"
        }
        
        # Act
        response = client.post("/api/shareholders/", json=invalid_data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.api.shareholders.get_db')
    def test_pagination_parameters(self, mock_get_db, client, mock_db_session, sample_shareholder, auth_headers):
        """Test des paramètres de pagination"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [sample_shareholder]
        
        # Act
        response = client.get("/api/shareholders/?skip=10&limit=5", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        mock_db_session.query.return_value.offset.assert_called_once_with(10)
        mock_db_session.query.return_value.offset.return_value.limit.assert_called_once_with(5)
    
    @patch('app.api.issuances.get_db')
    def test_issuances_pagination_parameters(self, mock_get_db, client, mock_db_session, sample_issuance, sample_shareholder, auth_headers):
        """Test des paramètres de pagination pour les émissions"""
        # Arrange
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.join.return_value.offset.return_value.limit.return_value.all.return_value = [
            (sample_issuance, sample_shareholder)
        ]
        
        # Act
        response = client.get("/api/issuances/?skip=5&limit=3", headers=auth_headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        mock_db_session.query.return_value.join.return_value.offset.assert_called_once_with(5)
        mock_db_session.query.return_value.join.return_value.offset.return_value.limit.assert_called_once_with(3)

