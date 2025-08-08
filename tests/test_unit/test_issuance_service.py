"""
Tests unitaires pour le service d'émissions d'actions
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4, UUID
from typing import List, Optional

from app.services.issuance_service import IssuanceService
from app.database.models import ShareholderProfile, ShareIssuance
from app.schemas.issuance import ShareIssuanceCreate, ShareIssuanceUpdate


@pytest.mark.unit
class TestIssuanceService:
    """Tests unitaires pour IssuanceService"""
    
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
            phone="+1234567890"
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
            certificate_path="/path/to/certificate.pdf"
        )
    
    @pytest.fixture
    def sample_issuance_create(self, sample_shareholder):
        """Données de création d'émission"""
        return ShareIssuanceCreate(
            shareholder_id=sample_shareholder.id,
            number_of_shares=100,
            price_per_share=Decimal("10.50"),
            total_amount=Decimal("1050.00"),
            issue_date=date.today()
        )
    
    def test_get_issuance_by_id_success(self, mock_db_session, sample_issuance):
        """Test de récupération d'émission par ID - succès"""
        # Arrange
        issuance_id = sample_issuance.id
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_issuance
        
        # Act
        result = IssuanceService.get_issuance_by_id(mock_db_session, issuance_id)
        
        # Assert
        assert result == sample_issuance
        mock_db_session.query.assert_called_once_with(ShareIssuance)
    
    def test_get_issuance_by_id_not_found(self, mock_db_session):
        """Test de récupération d'émission par ID - non trouvé"""
        # Arrange
        issuance_id = uuid4()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = IssuanceService.get_issuance_by_id(mock_db_session, issuance_id)
        
        # Assert
        assert result is None
    
    def test_get_issuances_success(self, mock_db_session, sample_issuance):
        """Test de récupération des émissions - succès"""
        # Arrange
        mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [sample_issuance]
        
        # Act
        result = IssuanceService.get_issuances(mock_db_session, skip=0, limit=10)
        
        # Assert
        assert result == [sample_issuance]
        assert len(result) == 1
    
    def test_get_issuances_empty(self, mock_db_session):
        """Test de récupération des émissions - liste vide"""
        # Arrange
        mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        # Act
        result = IssuanceService.get_issuances(mock_db_session, skip=0, limit=10)
        
        # Assert
        assert result == []
        assert len(result) == 0
    
    def test_get_issuances_by_shareholder_success(self, mock_db_session, sample_issuance, sample_shareholder):
        """Test de récupération des émissions par actionnaire - succès"""
        # Arrange
        shareholder_id = sample_shareholder.id
        mock_db_session.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [sample_issuance]
        
        # Act
        result = IssuanceService.get_issuances_by_shareholder(mock_db_session, shareholder_id, skip=0, limit=10)
        
        # Assert
        assert result == [sample_issuance]
        assert len(result) == 1
    
    @patch('app.services.issuance_service.CertificateService.generate_certificate')
    def test_create_issuance_success(self, mock_generate_certificate, mock_db_session, sample_shareholder, sample_issuance_create):
        """Test de création d'émission - succès"""
        # Arrange
        mock_generate_certificate.return_value = "/path/to/certificate.pdf"
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        # Mock de l'objet ShareIssuance créé
        mock_issuance = Mock(spec=ShareIssuance)
        mock_issuance.id = uuid4()
        mock_issuance.shareholder_id = sample_shareholder.id
        mock_issuance.number_of_shares = 100
        mock_issuance.price_per_share = Decimal("10.50")
        mock_issuance.total_amount = Decimal("1050.00")
        mock_issuance.certificate_path = "/path/to/certificate.pdf"
        mock_issuance.status = "issued"
        mock_issuance.created_at = datetime.now()
        mock_issuance.updated_at = datetime.now()
        
        # Mock de la création de l'objet ShareIssuance
        with patch('app.services.issuance_service.ShareIssuance') as mock_share_issuance_class:
            mock_share_issuance_class.return_value = mock_issuance
            
            # Act
            result = IssuanceService.create_issuance(mock_db_session, sample_issuance_create)
        
        # Assert
        assert result["shareholder_id"] == str(sample_shareholder.id)
        assert result["shares_count"] == 100
        assert result["share_price"] == 10.50
        assert result["total_amount"] == 1050.00
        assert result["certificate_path"] == "/path/to/certificate.pdf"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
    
    def test_create_issuance_shareholder_not_found(self, mock_db_session, sample_issuance_create):
        """Test de création d'émission - actionnaire non trouvé"""
        # Arrange
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Shareholder not found"):
            IssuanceService.create_issuance(mock_db_session, sample_issuance_create)
    
    def test_update_issuance_success(self, mock_db_session, sample_issuance):
        """Test de mise à jour d'émission - succès"""
        # Arrange
        issuance_id = sample_issuance.id
        update_data = ShareIssuanceUpdate(
            number_of_shares=200,
            price_per_share=Decimal("15.00"),
            total_amount=Decimal("3000.00"),
            status="issued"
        )
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_issuance
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        # Act
        result = IssuanceService.update_issuance(mock_db_session, issuance_id, update_data)
        
        # Assert
        assert result == sample_issuance
        assert sample_issuance.number_of_shares == 200
        assert sample_issuance.price_per_share == Decimal("15.00")
        assert sample_issuance.total_amount == Decimal("3000.00")
        mock_db_session.commit.assert_called_once()
    
    def test_update_issuance_not_found(self, mock_db_session):
        """Test de mise à jour d'émission - non trouvé"""
        # Arrange
        issuance_id = uuid4()
        update_data = ShareIssuanceUpdate(number_of_shares=200)
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = IssuanceService.update_issuance(mock_db_session, issuance_id, update_data)
        
        # Assert
        assert result is None
    
    def test_get_shareholder_summary_success(self, mock_db_session, sample_shareholder, sample_issuance):
        """Test de récupération du résumé d'actionnaire - succès"""
        # Arrange
        shareholder_id = sample_shareholder.id
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        mock_db_session.query.return_value.filter.return_value.all.return_value = [sample_issuance]
        
        # Act
        result = IssuanceService.get_shareholder_summary(mock_db_session, shareholder_id)
        
        # Assert
        assert result["shareholder_id"] == str(shareholder_id)
        assert result["total_shares"] == 100
        assert result["total_value"] == 1050.00
        assert result["total_issuances"] == 1
    
    def test_get_shareholder_summary_not_found(self, mock_db_session):
        """Test de récupération du résumé d'actionnaire - non trouvé"""
        # Arrange
        shareholder_id = uuid4()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Shareholder not found"):
            IssuanceService.get_shareholder_summary(mock_db_session, shareholder_id)
    
    def test_get_cap_table_summary_success(self, mock_db_session, sample_shareholder, sample_issuance):
        """Test de récupération du résumé de la cap table - succès"""
        # Arrange
        mock_db_session.query.return_value.all.return_value = [sample_shareholder]
        mock_db_session.query.return_value.filter.return_value.all.return_value = [sample_issuance]
        
        # Act
        result = IssuanceService.get_cap_table_summary(mock_db_session)
        
        # Assert
        assert result["total_shares"] == 100
        assert result["total_value"] == 1050.00
        assert result["total_shareholders"] == 1
        assert len(result["shareholders"]) == 1
    
    def test_get_cap_table_summary_empty(self, mock_db_session):
        """Test de récupération du résumé de la cap table - vide"""
        # Arrange
        mock_db_session.query.return_value.all.return_value = []
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        # Act
        result = IssuanceService.get_cap_table_summary(mock_db_session)
        
        # Assert
        assert result["total_shares"] == 0
        assert result["total_value"] == 0.0
        assert result["total_shareholders"] == 0
        assert len(result["shareholders"]) == 0
    
    def test_get_issuances_with_shareholder_info_success(self, mock_db_session, sample_shareholder, sample_issuance):
        """Test de récupération des émissions avec info actionnaire - succès"""
        # Arrange
        mock_db_session.query.return_value.join.return_value.offset.return_value.limit.return_value.all.return_value = [
            (sample_issuance, sample_shareholder)
        ]
        
        # Act
        result = IssuanceService.get_issuances_with_shareholder_info(mock_db_session, skip=0, limit=10)
        
        # Assert
        assert len(result) == 1
        assert result[0]["id"] == str(sample_issuance.id)
        assert result[0]["shareholder_id"] == str(sample_shareholder.id)
        assert result[0]["shareholder"]["username"] == sample_shareholder.username
    
    def test_get_issuances_with_shareholder_info_filtered(self, mock_db_session, sample_shareholder, sample_issuance):
        """Test de récupération des émissions avec filtre actionnaire"""
        # Arrange
        shareholder_id = sample_shareholder.id
        mock_db_session.query.return_value.join.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            (sample_issuance, sample_shareholder)
        ]
        
        # Act
        result = IssuanceService.get_issuances_with_shareholder_info(
            mock_db_session, skip=0, limit=10, shareholder_id=shareholder_id
        )
        
        # Assert
        assert len(result) == 1
        assert result[0]["shareholder_id"] == str(shareholder_id)
    
    def test_calculate_total_amount(self, mock_db_session, sample_shareholder):
        """Test du calcul du montant total"""
        # Arrange
        number_of_shares = 100
        price_per_share = Decimal("10.50")
        expected_total = number_of_shares * price_per_share
        
        # Act
        total = number_of_shares * float(price_per_share)
        
        # Assert
        assert total == 1050.0
        assert total == float(expected_total)
    
    def test_validate_issuance_data(self, mock_db_session, sample_shareholder):
        """Test de validation des données d'émission"""
        # Arrange
        valid_data = ShareIssuanceCreate(
            shareholder_id=sample_shareholder.id,
            number_of_shares=100,
            price_per_share=Decimal("10.50"),
            total_amount=Decimal("1050.00"),
            issue_date=date.today()
        )
        
        # Act & Assert
        assert valid_data.number_of_shares > 0
        assert valid_data.price_per_share >= 0
        assert valid_data.total_amount >= 0
        assert valid_data.shareholder_id is not None
    
    def test_validate_issuance_data_invalid(self):
        """Test de validation des données d'émission - invalides"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError):
            ShareIssuanceCreate(
                shareholder_id=uuid4(),
                number_of_shares=-100,  # Invalide
                price_per_share=Decimal("10.50"),
                total_amount=Decimal("1050.00"),
                issue_date=date.today()
            )
    
    @patch('app.services.issuance_service.CertificateService.generate_certificate')
    def test_create_issuance_with_certificate_error(self, mock_generate_certificate, mock_db_session, sample_shareholder, sample_issuance_create):
        """Test de création d'émission avec erreur de certificat"""
        # Arrange
        mock_generate_certificate.side_effect = Exception("Certificate generation failed")
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.rollback.return_value = None
        
        # Mock de l'objet ShareIssuance créé
        mock_issuance = Mock(spec=ShareIssuance)
        mock_issuance.id = uuid4()
        mock_issuance.shareholder_id = sample_shareholder.id
        mock_issuance.number_of_shares = 100
        mock_issuance.price_per_share = Decimal("10.50")
        mock_issuance.total_amount = Decimal("1050.00")
        mock_issuance.status = "issued"
        
        with patch('app.services.issuance_service.ShareIssuance') as mock_share_issuance_class:
            mock_share_issuance_class.return_value = mock_issuance
            
            # Act & Assert
            with pytest.raises(Exception, match="Certificate generation failed"):
                IssuanceService.create_issuance(mock_db_session, sample_issuance_create)
            
            mock_db_session.rollback.assert_called_once()
    
    def test_get_issuances_pagination(self, mock_db_session, sample_issuance):
        """Test de pagination des émissions"""
        # Arrange
        mock_db_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [sample_issuance]
        
        # Act
        result = IssuanceService.get_issuances(mock_db_session, skip=10, limit=5)
        
        # Assert
        assert result == [sample_issuance]
        mock_db_session.query.return_value.offset.assert_called_once_with(10)
        mock_db_session.query.return_value.offset.return_value.limit.assert_called_once_with(5)
    
    def test_get_issuances_by_shareholder_pagination(self, mock_db_session, sample_issuance, sample_shareholder):
        """Test de pagination des émissions par actionnaire"""
        # Arrange
        shareholder_id = sample_shareholder.id
        mock_db_session.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [sample_issuance]
        
        # Act
        result = IssuanceService.get_issuances_by_shareholder(mock_db_session, shareholder_id, skip=5, limit=3)
        
        # Assert
        assert result == [sample_issuance]
        mock_db_session.query.return_value.filter.return_value.offset.assert_called_once_with(5)
        mock_db_session.query.return_value.filter.return_value.offset.return_value.limit.assert_called_once_with(3)



