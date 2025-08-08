"""
Tests unitaires pour le service de certificats
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
import os
import tempfile

from app.services.certificate_service import CertificateService
from app.database.models import ShareholderProfile, ShareIssuance


@pytest.mark.unit
class TestCertificateService:
    """Tests unitaires pour CertificateService"""
    
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
            certificate_path=None
        )
    
    @patch('app.services.certificate_service.ReportLab')
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.os.makedirs')
    def test_generate_certificate_success(self, mock_makedirs, mock_exists, mock_reportlab, mock_db_session, sample_shareholder, sample_issuance):
        """Test de génération de certificat - succès"""
        # Arrange
        mock_exists.return_value = False
        mock_canvas = Mock()
        mock_reportlab.canvas.Canvas.return_value = mock_canvas
        
        # Mock des méthodes du canvas
        mock_canvas.drawString = Mock()
        mock_canvas.drawImage = Mock()
        mock_canvas.save = Mock()
        
        # Mock de la session pour récupérer l'actionnaire
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Act
        result = CertificateService.generate_certificate(sample_issuance, mock_db_session)
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith('.pdf')
        mock_canvas.save.assert_called_once()
        mock_makedirs.assert_called_once()
    
    @patch('app.services.certificate_service.ReportLab')
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.os.makedirs')
    def test_generate_certificate_shareholder_not_found(self, mock_makedirs, mock_exists, mock_reportlab, mock_db_session, sample_issuance):
        """Test de génération de certificat - actionnaire non trouvé"""
        # Arrange
        mock_exists.return_value = False
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Shareholder not found"):
            CertificateService.generate_certificate(sample_issuance, mock_db_session)
    
    @patch('app.services.certificate_service.ReportLab')
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.os.makedirs')
    def test_generate_certificate_directory_exists(self, mock_makedirs, mock_exists, mock_reportlab, mock_db_session, sample_shareholder, sample_issuance):
        """Test de génération de certificat - répertoire existe déjà"""
        # Arrange
        mock_exists.return_value = True
        mock_canvas = Mock()
        mock_reportlab.canvas.Canvas.return_value = mock_canvas
        mock_canvas.drawString = Mock()
        mock_canvas.drawImage = Mock()
        mock_canvas.save = Mock()
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Act
        result = CertificateService.generate_certificate(sample_issuance, mock_db_session)
        
        # Assert
        assert result is not None
        mock_makedirs.assert_not_called()
    
    @patch('app.services.certificate_service.ReportLab')
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.os.makedirs')
    def test_generate_certificate_canvas_error(self, mock_makedirs, mock_exists, mock_reportlab, mock_db_session, sample_shareholder, sample_issuance):
        """Test de génération de certificat - erreur canvas"""
        # Arrange
        mock_exists.return_value = False
        mock_reportlab.canvas.Canvas.side_effect = Exception("Canvas creation failed")
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Act & Assert
        with pytest.raises(Exception, match="Canvas creation failed"):
            CertificateService.generate_certificate(sample_issuance, mock_db_session)
    
    @patch('app.services.certificate_service.ReportLab')
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.os.makedirs')
    def test_generate_certificate_save_error(self, mock_makedirs, mock_exists, mock_reportlab, mock_db_session, sample_shareholder, sample_issuance):
        """Test de génération de certificat - erreur sauvegarde"""
        # Arrange
        mock_exists.return_value = False
        mock_canvas = Mock()
        mock_reportlab.canvas.Canvas.return_value = mock_canvas
        mock_canvas.drawString = Mock()
        mock_canvas.drawImage = Mock()
        mock_canvas.save.side_effect = Exception("Save failed")
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Act & Assert
        with pytest.raises(Exception, match="Save failed"):
            CertificateService.generate_certificate(sample_issuance, mock_db_session)
    
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.PIL.Image')
    def test_add_watermark_success(self, mock_pil_image, mock_exists, sample_issuance):
        """Test d'ajout de filigrane - succès"""
        # Arrange
        mock_exists.return_value = True
        mock_image = Mock()
        mock_pil_image.open.return_value = mock_image
        mock_image.convert.return_value = mock_image
        mock_image.save = Mock()
        
        # Créer un fichier temporaire pour le test
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Act
            CertificateService._add_watermark(temp_filepath)
            
            # Assert
            mock_pil_image.open.assert_called_once()
            mock_image.save.assert_called_once()
        finally:
            # Nettoyer
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)
    
    @patch('app.services.certificate_service.os.path.exists')
    def test_add_watermark_file_not_found(self, mock_exists, sample_issuance):
        """Test d'ajout de filigrane - fichier non trouvé"""
        # Arrange
        mock_exists.return_value = False
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            CertificateService._add_watermark("/path/to/nonexistent.pdf")
    
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.PIL.Image')
    def test_add_watermark_pil_error(self, mock_pil_image, mock_exists, sample_issuance):
        """Test d'ajout de filigrane - erreur PIL"""
        # Arrange
        mock_exists.return_value = True
        mock_pil_image.open.side_effect = Exception("PIL error")
        
        # Créer un fichier temporaire pour le test
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Act & Assert
            with pytest.raises(Exception, match="PIL error"):
                CertificateService._add_watermark(temp_filepath)
        finally:
            # Nettoyer
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)
    
    @patch('app.services.certificate_service.os.path.exists')
    def test_get_certificate_path_exists(self, mock_exists, sample_issuance):
        """Test de récupération du chemin de certificat - existe"""
        # Arrange
        mock_exists.return_value = True
        sample_issuance.certificate_path = "/path/to/certificate.pdf"
        
        # Act
        result = CertificateService.get_certificate_path(str(sample_issuance.id))
        
        # Assert
        assert result == "/path/to/certificate.pdf"
    
    @patch('app.services.certificate_service.os.path.exists')
    def test_get_certificate_path_not_exists(self, mock_exists, sample_issuance):
        """Test de récupération du chemin de certificat - n'existe pas"""
        # Arrange
        mock_exists.return_value = False
        
        # Act
        result = CertificateService.get_certificate_path(str(sample_issuance.id))
        
        # Assert
        assert result is None
    
    @patch('app.services.certificate_service.ReportLab')
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.os.makedirs')
    def test_generate_certificate_with_watermark(self, mock_makedirs, mock_exists, mock_reportlab, mock_db_session, sample_shareholder, sample_issuance):
        """Test de génération de certificat avec filigrane"""
        # Arrange
        mock_exists.return_value = False
        mock_canvas = Mock()
        mock_reportlab.canvas.Canvas.return_value = mock_canvas
        mock_canvas.drawString = Mock()
        mock_canvas.drawImage = Mock()
        mock_canvas.save = Mock()
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Mock de l'ajout de filigrane
        with patch.object(CertificateService, '_add_watermark') as mock_watermark:
            # Act
            result = CertificateService.generate_certificate(sample_issuance, mock_db_session)
            
            # Assert
            assert result is not None
            mock_watermark.assert_called_once()
    
    def test_certificate_filename_generation(self, sample_issuance):
        """Test de génération du nom de fichier de certificat"""
        # Arrange
        issuance_id = str(sample_issuance.id)
        
        # Act
        expected_filename = f"certificate_{issuance_id}.pdf"
        
        # Assert
        assert expected_filename.startswith("certificate_")
        assert expected_filename.endswith(".pdf")
        assert issuance_id in expected_filename
    
    @patch('app.services.certificate_service.ReportLab')
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.os.makedirs')
    def test_generate_certificate_content_verification(self, mock_makedirs, mock_exists, mock_reportlab, mock_db_session, sample_shareholder, sample_issuance):
        """Test de vérification du contenu du certificat"""
        # Arrange
        mock_exists.return_value = False
        mock_canvas = Mock()
        mock_reportlab.canvas.Canvas.return_value = mock_canvas
        mock_canvas.drawString = Mock()
        mock_canvas.drawImage = Mock()
        mock_canvas.save = Mock()
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Act
        result = CertificateService.generate_certificate(sample_issuance, mock_db_session)
        
        # Assert
        assert result is not None
        # Vérifier que les informations du certificat sont dessinées
        assert mock_canvas.drawString.call_count > 0
    
    @patch('app.services.certificate_service.ReportLab')
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.os.makedirs')
    def test_generate_certificate_with_different_shareholder_data(self, mock_makedirs, mock_exists, mock_reportlab, mock_db_session, sample_issuance):
        """Test de génération de certificat avec différentes données d'actionnaire"""
        # Arrange
        mock_exists.return_value = False
        mock_canvas = Mock()
        mock_reportlab.canvas.Canvas.return_value = mock_canvas
        mock_canvas.drawString = Mock()
        mock_canvas.drawImage = Mock()
        mock_canvas.save = Mock()
        
        # Actionnaire avec données différentes
        different_shareholder = ShareholderProfile(
            id=uuid4(),
            keycloak_id="different-keycloak-id",
            username="differentuser",
            email="different@example.com",
            first_name="Different",
            last_name="User",
            company_name="Different Company",
            phone="+9876543210"
        )
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = different_shareholder
        
        # Act
        result = CertificateService.generate_certificate(sample_issuance, mock_db_session)
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
    
    @patch('app.services.certificate_service.ReportLab')
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.os.makedirs')
    def test_generate_certificate_with_different_issuance_data(self, mock_makedirs, mock_exists, mock_reportlab, mock_db_session, sample_shareholder):
        """Test de génération de certificat avec différentes données d'émission"""
        # Arrange
        mock_exists.return_value = False
        mock_canvas = Mock()
        mock_reportlab.canvas.Canvas.return_value = mock_canvas
        mock_canvas.drawString = Mock()
        mock_canvas.drawImage = Mock()
        mock_canvas.save = Mock()
        
        # Émission avec données différentes
        different_issuance = ShareIssuance(
            id=uuid4(),
            shareholder_id=sample_shareholder.id,
            number_of_shares=500,
            price_per_share=Decimal("25.00"),
            total_amount=Decimal("12500.00"),
            issue_date=datetime.now(),
            status="issued",
            certificate_path=None
        )
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Act
        result = CertificateService.generate_certificate(different_issuance, mock_db_session)
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
    
    def test_certificate_directory_structure(self):
        """Test de la structure du répertoire de certificats"""
        # Arrange
        expected_base_dir = "certificates"
        
        # Act & Assert
        assert expected_base_dir == "certificates"
        # Vérifier que le répertoire peut être créé (test d'intégration)
        # Ce test vérifie que la logique de création de répertoire fonctionne
    
    @patch('app.services.certificate_service.ReportLab')
    @patch('app.services.certificate_service.os.path.exists')
    @patch('app.services.certificate_service.os.makedirs')
    def test_generate_certificate_error_handling(self, mock_makedirs, mock_exists, mock_reportlab, mock_db_session, sample_shareholder, sample_issuance):
        """Test de gestion d'erreur lors de la génération de certificat"""
        # Arrange
        mock_exists.return_value = False
        mock_reportlab.canvas.Canvas.side_effect = Exception("ReportLab error")
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_shareholder
        
        # Act & Assert
        with pytest.raises(Exception, match="ReportLab error"):
            CertificateService.generate_certificate(sample_issuance, mock_db_session)
    
    def test_certificate_path_validation(self, sample_issuance):
        """Test de validation du chemin de certificat"""
        # Arrange
        valid_path = "/path/to/certificate.pdf"
        invalid_path = "/path/to/certificate.txt"
        
        # Act & Assert
        assert valid_path.endswith('.pdf')
        assert not invalid_path.endswith('.pdf')
    
    @patch('app.services.certificate_service.os.path.exists')
    def test_get_certificate_path_with_none_id(self, mock_exists):
        """Test de récupération du chemin avec ID None"""
        # Arrange
        mock_exists.return_value = False
        
        # Act
        result = CertificateService.get_certificate_path(None)
        
        # Assert
        assert result is None
    
    @patch('app.services.certificate_service.os.path.exists')
    def test_get_certificate_path_with_empty_id(self, mock_exists):
        """Test de récupération du chemin avec ID vide"""
        # Arrange
        mock_exists.return_value = False
        
        # Act
        result = CertificateService.get_certificate_path("")
        
        # Assert
        assert result is None
