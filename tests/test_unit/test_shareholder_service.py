"""
Tests unitaires pour le service d'actionnaires
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from uuid import uuid4, UUID
from typing import List, Optional

from app.services.user_service import UserService
from app.database.models import ShareholderProfile, ShareIssuance
from app.schemas.user import UserCreate, UserUpdate


@pytest.mark.unit
class TestShareholderService:
    """Tests unitaires pour le service d'actionnaires"""
    
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
    def sample_shareholder_create(self):
        """Données de création d'actionnaire"""
        return UserCreate(
            username="newuser",
            email="newuser@example.com",
            first_name="New",
            last_name="User",
            company_name="New Company",
            phone="+9876543210"
        )
    
    @pytest.fixture
    def sample_shareholder_update(self):
        """Données de mise à jour d'actionnaire"""
        return UserUpdate(
            first_name="Updated",
            last_name="User",
            company_name="Updated Company",
            phone="+1111111111"
        )
    
    def test_get_shareholder_by_id_success(self, mock_db_session, sample_shareholder):
        """Test de récupération d'actionnaire par ID - succès"""
        # Arrange
        shareholder_id = sample_shareholder.id
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Act
        result = UserService.get_user_by_id(mock_db_session, shareholder_id)
        
        # Assert
        assert result == sample_shareholder
        mock_db_session.query.assert_called_once_with(ShareholderProfile)
    
    def test_get_shareholder_by_id_not_found(self, mock_db_session):
        """Test de récupération d'actionnaire par ID - non trouvé"""
        # Arrange
        shareholder_id = uuid4()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = UserService.get_user_by_id(mock_db_session, shareholder_id)
        
        # Assert
        assert result is None
    
    def test_get_shareholder_by_username_success(self, mock_db_session, sample_shareholder):
        """Test de récupération d'actionnaire par username - succès"""
        # Arrange
        username = sample_shareholder.username
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Act
        result = UserService.get_user_by_username(mock_db_session, username)
        
        # Assert
        assert result == sample_shareholder
        mock_db_session.query.assert_called_once_with(ShareholderProfile)
    
    def test_get_shareholder_by_username_not_found(self, mock_db_session):
        """Test de récupération d'actionnaire par username - non trouvé"""
        # Arrange
        username = "nonexistent"
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = UserService.get_user_by_username(mock_db_session, username)
        
        # Assert
        assert result is None
    
    def test_get_shareholder_by_email_success(self, mock_db_session, sample_shareholder):
        """Test de récupération d'actionnaire par email - succès"""
        # Arrange
        email = sample_shareholder.email
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Act
        result = UserService.get_user_by_email(mock_db_session, email)
        
        # Assert
        assert result == sample_shareholder
        mock_db_session.query.assert_called_once_with(ShareholderProfile)
    
    def test_get_shareholder_by_email_not_found(self, mock_db_session):
        """Test de récupération d'actionnaire par email - non trouvé"""
        # Arrange
        email = "nonexistent@example.com"
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = UserService.get_user_by_email(mock_db_session, email)
        
        # Assert
        assert result is None
    
    def test_get_shareholders_success(self, mock_db_session, sample_shareholder):
        """Test de récupération des actionnaires - succès"""
        # Arrange
        mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [sample_shareholder]
        
        # Act
        result = UserService.get_shareholders(mock_db_session, skip=0, limit=10)
        
        # Assert
        assert result == [sample_shareholder]
        assert len(result) == 1
    
    def test_get_shareholders_empty(self, mock_db_session):
        """Test de récupération des actionnaires - liste vide"""
        # Arrange
        mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        # Act
        result = UserService.get_shareholders(mock_db_session, skip=0, limit=10)
        
        # Assert
        assert result == []
        assert len(result) == 0
    
    def test_create_shareholder_success(self, mock_db_session, sample_shareholder_create):
        """Test de création d'actionnaire - succès"""
        # Arrange
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        # Mock de l'objet ShareholderProfile créé
        mock_shareholder = Mock(spec=ShareholderProfile)
        mock_shareholder.id = uuid4()
        mock_shareholder.username = sample_shareholder_create.username
        mock_shareholder.email = sample_shareholder_create.email
        mock_shareholder.first_name = sample_shareholder_create.first_name
        mock_shareholder.last_name = sample_shareholder_create.last_name
        mock_shareholder.company_name = sample_shareholder_create.company_name
        mock_shareholder.phone = sample_shareholder_create.phone
        
        # Mock de la création de l'objet ShareholderProfile
        with patch('app.services.user_service.ShareholderProfile') as mock_shareholder_class:
            mock_shareholder_class.return_value = mock_shareholder
            
            # Act
            result = UserService.create_user(mock_db_session, sample_shareholder_create)
        
        # Assert
        assert result == mock_shareholder
        assert result.username == sample_shareholder_create.username
        assert result.email == sample_shareholder_create.email
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_create_shareholder_duplicate_username(self, mock_db_session, sample_shareholder_create):
        """Test de création d'actionnaire - username en double"""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = Mock()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Username already exists"):
            UserService.create_user(mock_db_session, sample_shareholder_create)
    
    def test_create_shareholder_duplicate_email(self, mock_db_session, sample_shareholder_create):
        """Test de création d'actionnaire - email en double"""
        # Arrange
        # Premier appel retourne None (username OK), deuxième appel retourne un utilisateur (email en double)
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [None, Mock()]
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already exists"):
            UserService.create_user(mock_db_session, sample_shareholder_create)
    
    def test_update_shareholder_success(self, mock_db_session, sample_shareholder, sample_shareholder_update):
        """Test de mise à jour d'actionnaire - succès"""
        # Arrange
        shareholder_id = sample_shareholder.id
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        # Act
        result = UserService.update_user(mock_db_session, shareholder_id, sample_shareholder_update)
        
        # Assert
        assert result == sample_shareholder
        assert sample_shareholder.first_name == sample_shareholder_update.first_name
        assert sample_shareholder.last_name == sample_shareholder_update.last_name
        assert sample_shareholder.company_name == sample_shareholder_update.company_name
        assert sample_shareholder.phone == sample_shareholder_update.phone
        mock_db_session.commit.assert_called_once()
    
    def test_update_shareholder_not_found(self, mock_db_session, sample_shareholder_update):
        """Test de mise à jour d'actionnaire - non trouvé"""
        # Arrange
        shareholder_id = uuid4()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = UserService.update_user(mock_db_session, shareholder_id, sample_shareholder_update)
        
        # Assert
        assert result is None
    
    def test_delete_shareholder_success(self, mock_db_session, sample_shareholder):
        """Test de suppression d'actionnaire - succès"""
        # Arrange
        shareholder_id = sample_shareholder.id
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        mock_db_session.delete.return_value = None
        mock_db_session.commit.return_value = None
        
        # Act
        result = UserService.delete_user(mock_db_session, shareholder_id)
        
        # Assert
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_shareholder)
        mock_db_session.commit.assert_called_once()
    
    def test_delete_shareholder_not_found(self, mock_db_session):
        """Test de suppression d'actionnaire - non trouvé"""
        # Arrange
        shareholder_id = uuid4()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = UserService.delete_user(mock_db_session, shareholder_id)
        
        # Assert
        assert result is False
    
    def test_get_shareholder_with_shares_success(self, mock_db_session, sample_shareholder):
        """Test de récupération d'actionnaire avec actions - succès"""
        # Arrange
        shareholder_id = sample_shareholder.id
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Mock des actions
        mock_issuance = Mock(spec=ShareIssuance)
        mock_issuance.number_of_shares = 100
        mock_issuance.price_per_share = 10.50
        mock_issuance.total_amount = 1050.00
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_issuance]
        
        # Act
        result = UserService.get_user_with_shares(mock_db_session, shareholder_id)
        
        # Assert
        assert result is not None
        assert result["id"] == str(shareholder_id)
        assert result["username"] == sample_shareholder.username
        assert "shares" in result
    
    def test_get_shareholder_with_shares_not_found(self, mock_db_session):
        """Test de récupération d'actionnaire avec actions - non trouvé"""
        # Arrange
        shareholder_id = uuid4()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = UserService.get_user_with_shares(mock_db_session, shareholder_id)
        
        # Assert
        assert result is None
    
    def test_get_shareholders_with_shares_success(self, mock_db_session, sample_shareholder):
        """Test de récupération des actionnaires avec actions - succès"""
        # Arrange
        mock_db_session.query.return_value.outerjoin.return_value.offset.return_value.limit.return_value.all.return_value = [
            (sample_shareholder, None)
        ]
        
        # Act
        result = UserService.get_shareholders_with_shares(mock_db_session, skip=0, limit=10)
        
        # Assert
        assert len(result) == 1
        assert result[0]["id"] == str(sample_shareholder.id)
        assert result[0]["username"] == sample_shareholder.username
    
    def test_get_shareholders_with_shares_empty(self, mock_db_session):
        """Test de récupération des actionnaires avec actions - liste vide"""
        # Arrange
        mock_db_session.query.return_value.outerjoin.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        # Act
        result = UserService.get_shareholders_with_shares(mock_db_session, skip=0, limit=10)
        
        # Assert
        assert result == []
        assert len(result) == 0
    
    def test_get_shareholder_summary_success(self, mock_db_session, sample_shareholder):
        """Test de récupération du résumé d'actionnaire - succès"""
        # Arrange
        shareholder_id = sample_shareholder.id
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Mock des actions
        mock_issuance = Mock(spec=ShareIssuance)
        mock_issuance.number_of_shares = 100
        mock_issuance.price_per_share = 10.50
        mock_issuance.total_amount = 1050.00
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_issuance]
        
        # Act
        result = UserService.get_shareholder_summary(mock_db_session, shareholder_id)
        
        # Assert
        assert result is not None
        assert result["shareholder_id"] == str(shareholder_id)
        assert result["total_shares"] == 100
        assert result["total_value"] == 1050.00
    
    def test_get_shareholder_summary_not_found(self, mock_db_session):
        """Test de récupération du résumé d'actionnaire - non trouvé"""
        # Arrange
        shareholder_id = uuid4()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = UserService.get_shareholder_summary(mock_db_session, shareholder_id)
        
        # Assert
        assert result is None
    
    def test_validate_shareholder_data(self, sample_shareholder_create):
        """Test de validation des données d'actionnaire"""
        # Arrange & Act & Assert
        assert sample_shareholder_create.username is not None
        assert sample_shareholder_create.email is not None
        assert "@" in sample_shareholder_create.email
        assert sample_shareholder_create.first_name is not None
        assert sample_shareholder_create.last_name is not None
    
    def test_validate_shareholder_data_invalid_email(self):
        """Test de validation des données d'actionnaire - email invalide"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            UserCreate(
                username="testuser",
                email="invalid-email",
                first_name="Test",
                last_name="User"
            )
    
    def test_validate_shareholder_data_empty_username(self):
        """Test de validation des données d'actionnaire - username vide"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            UserCreate(
                username="",
                email="test@example.com",
                first_name="Test",
                last_name="User"
            )
    
    def test_get_shareholders_pagination(self, mock_db_session, sample_shareholder):
        """Test de pagination des actionnaires"""
        # Arrange
        mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [sample_shareholder]
        
        # Act
        result = UserService.get_shareholders(mock_db_session, skip=10, limit=5)
        
        # Assert
        assert result == [sample_shareholder]
        mock_db_session.query.return_value.offset.assert_called_once_with(10)
        mock_db_session.query.return_value.offset.return_value.limit.assert_called_once_with(5)
    
    def test_get_shareholders_with_shares_pagination(self, mock_db_session, sample_shareholder):
        """Test de pagination des actionnaires avec actions"""
        # Arrange
        mock_db_session.query.return_value.outerjoin.return_value.offset.return_value.limit.return_value.all.return_value = [
            (sample_shareholder, None)
        ]
        
        # Act
        result = UserService.get_shareholders_with_shares(mock_db_session, skip=5, limit=3)
        
        # Assert
        assert len(result) == 1
        mock_db_session.query.return_value.outerjoin.return_value.offset.assert_called_once_with(5)
        mock_db_session.query.return_value.outerjoin.return_value.offset.return_value.limit.assert_called_once_with(3)
    
    def test_shareholder_data_serialization(self, sample_shareholder):
        """Test de sérialisation des données d'actionnaire"""
        # Arrange
        shareholder_dict = {
            "id": str(sample_shareholder.id),
            "username": sample_shareholder.username,
            "email": sample_shareholder.email,
            "first_name": sample_shareholder.first_name,
            "last_name": sample_shareholder.last_name,
            "company_name": sample_shareholder.company_name,
            "phone": sample_shareholder.phone
        }
        
        # Act & Assert
        assert shareholder_dict["id"] == str(sample_shareholder.id)
        assert shareholder_dict["username"] == sample_shareholder.username
        assert shareholder_dict["email"] == sample_shareholder.email
        assert isinstance(shareholder_dict["id"], str)
    
    def test_shareholder_update_partial(self, mock_db_session, sample_shareholder):
        """Test de mise à jour partielle d'actionnaire"""
        # Arrange
        shareholder_id = sample_shareholder.id
        partial_update = UserUpdate(first_name="Updated")
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        # Act
        result = UserService.update_user(mock_db_session, shareholder_id, partial_update)
        
        # Assert
        assert result == sample_shareholder
        assert sample_shareholder.first_name == "Updated"
        # Les autres champs ne doivent pas être modifiés
        assert sample_shareholder.last_name == "User"
        assert sample_shareholder.company_name == "Test Company"
    
    def test_shareholder_search_functionality(self, mock_db_session, sample_shareholder):
        """Test de fonctionnalité de recherche d'actionnaire"""
        # Arrange
        search_term = "test"
        mock_db_session.query.return_value.filter.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [sample_shareholder]
        
        # Act
        # Simuler une recherche par nom ou email
        result = UserService.get_shareholders(mock_db_session, skip=0, limit=10)
        
        # Assert
        assert result == [sample_shareholder]
        assert len(result) == 1



