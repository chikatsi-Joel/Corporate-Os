"""
Tests unitaires pour le service d'audit
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from audit.service.audit_service import AuditService
from app.database.models import AuditEvent
from app.schemas.audit import AuditEventSummary
from core.event_type import EventTypeEnum


class TestAuditService:
    """Tests pour AuditService"""

    @pytest.fixture
    def mock_db(self):
        """Fixture pour une session de base de données mockée"""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_audit_event(self):
        """Fixture pour un événement d'audit d'exemple"""
        event = Mock(spec=AuditEvent)
        event.id = 1
        event.user_id = "user123"
        event.action = EventTypeEnum.USER_LOGIN.value
        event.resource_type = "user"
        event.resource_id = "user123"
        event.description = "Connexion utilisateur"
        event.event_data = json.dumps({"user_email": "user@example.com"})
        event.previous_data = None
        event.status = "processed"
        event.created_at = datetime.utcnow()
        event.processed_at = datetime.utcnow()
        return event

    @patch('audit.service.audit_service.get_audit_publisher')
    @patch('audit.service.audit_service.get_notification_publisher')
    def test_create_audit_event_success(self, mock_notification_publisher, mock_audit_publisher, mock_db, sample_audit_event):
        """Test de création réussie d'un événement d'audit"""
        # Mock setup
        mock_audit_publisher_instance = Mock()
        mock_audit_publisher.return_value = mock_audit_publisher_instance
        mock_audit_publisher_instance.publish.return_value = True
        
        mock_notification_publisher_instance = Mock()
        mock_notification_publisher.return_value = mock_notification_publisher_instance
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        mock_db.refresh.return_value = sample_audit_event
        
        # Test
        result = AuditService.create_audit_event(
            db=mock_db,
            user_id="user123",
            action="create",
            resource_type="shareholder",
            resource_id="shareholder123",
            description="Création d'un actionnaire",
            event_data={"username": "john.doe"},
            previous_data=None
        )
        
        # Assertions
        assert result == sample_audit_event
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('audit.service.audit_service.get_audit_publisher')
    def test_create_audit_event_database_error(self, mock_audit_publisher, mock_db):
        """Test de création d'événement d'audit avec erreur de base de données"""
        # Mock setup
        mock_audit_publisher_instance = Mock()
        mock_audit_publisher.return_value = mock_audit_publisher_instance
        
        mock_db.add = Mock()
        mock_db.commit = Mock(side_effect=SQLAlchemyError("Database error"))
        mock_db.rollback = Mock()
        
        # Test
        result = AuditService.create_audit_event(
            db=mock_db,
            user_id="user123",
            action="create",
            resource_type="shareholder",
            resource_id="shareholder123",
            description="Création d'un actionnaire"
        )
        
        # Assertions
        assert result is None
        mock_db.rollback.assert_called_once()

    @patch('audit.service.audit_service.get_audit_publisher')
    def test_log_user_login_success(self, mock_audit_publisher, mock_db):
        """Test de journalisation de connexion utilisateur"""
        # Mock setup
        mock_audit_publisher_instance = Mock()
        mock_audit_publisher.return_value = mock_audit_publisher_instance
        mock_audit_publisher_instance.publish_user_login.return_value = True
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Test
        result = AuditService.log_user_login(
            db=mock_db,
            user_id="user123",
            user_email="user@example.com",
            user_role="admin",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        # Assertions
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_audit_publisher_instance.publish_user_login.assert_called_once_with(
            "user123", "user@example.com", "admin", "192.168.1.1", "Mozilla/5.0"
        )

    @patch('audit.service.audit_service.get_audit_publisher')
    def test_log_user_logout_success(self, mock_audit_publisher, mock_db):
        """Test de journalisation de déconnexion utilisateur"""
        # Mock setup
        mock_audit_publisher_instance = Mock()
        mock_audit_publisher.return_value = mock_audit_publisher_instance
        mock_audit_publisher_instance.publish_user_logout.return_value = True
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Test
        result = AuditService.log_user_logout(
            db=mock_db,
            user_id="user123",
            user_email="user@example.com",
            session_duration=3600
        )
        
        # Assertions
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_audit_publisher_instance.publish_user_logout.assert_called_once_with(
            "user123", "user@example.com", 3600
        )

    @patch('audit.service.audit_service.get_audit_publisher')
    def test_log_shareholder_created_success(self, mock_audit_publisher, mock_db):
        """Test de journalisation de création d'actionnaire"""
        # Mock setup
        mock_audit_publisher_instance = Mock()
        mock_audit_publisher.return_value = mock_audit_publisher_instance
        mock_audit_publisher_instance.publish_shareholder_created.return_value = True
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        shareholder_data = {
            "id": "123",
            "username": "john.doe",
            "email": "john@example.com"
        }
        
        # Test
        result = AuditService.log_shareholder_created(
            db=mock_db,
            user_id="admin123",
            shareholder_data=shareholder_data
        )
        
        # Assertions
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_audit_publisher_instance.publish_shareholder_created.assert_called_once_with(
            "admin123", shareholder_data
        )

    @patch('audit.service.audit_service.get_audit_publisher')
    @patch('audit.service.audit_service.get_notification_publisher')
    def test_log_share_issued_success(self, mock_notification_publisher, mock_audit_publisher, mock_db):
        """Test de journalisation d'émission d'actions"""
        # Mock setup
        mock_audit_publisher_instance = Mock()
        mock_audit_publisher.return_value = mock_audit_publisher_instance
        mock_audit_publisher_instance.publish_share_issued.return_value = True
        
        mock_notification_publisher_instance = Mock()
        mock_notification_publisher.return_value = mock_notification_publisher_instance
        mock_notification_publisher_instance.publish_share_issuance_notification.return_value = True
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        share_data = {
            "id": "456",
            "number_of_shares": 100,
            "price_per_share": 10.0,
            "total_amount": 1000.0,
            "shareholder_name": "John Doe"
        }
        
        # Test
        result = AuditService.log_share_issued(
            db=mock_db,
            user_id="admin123",
            shareholder_id="user123",
            share_data=share_data
        )
        
        # Assertions
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_audit_publisher_instance.publish_share_issued.assert_called_once_with(
            "admin123", "user123", share_data
        )
        mock_notification_publisher_instance.publish_share_issuance_notification.assert_called_once()

    @patch('audit.service.audit_service.get_audit_publisher')
    @patch('audit.service.audit_service.get_notification_publisher')
    def test_log_certificate_generated_success(self, mock_notification_publisher, mock_audit_publisher, mock_db):
        """Test de journalisation de génération de certificat"""
        # Mock setup
        mock_audit_publisher_instance = Mock()
        mock_audit_publisher.return_value = mock_audit_publisher_instance
        mock_audit_publisher_instance.publish_certificate_generated.return_value = True
        
        mock_notification_publisher_instance = Mock()
        mock_notification_publisher.return_value = mock_notification_publisher_instance
        mock_notification_publisher_instance.publish_certificate_notification.return_value = True
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Test
        result = AuditService.log_certificate_generated(
            db=mock_db,
            user_id="admin123",
            shareholder_id="user123",
            certificate_path="/path/to/certificate.pdf"
        )
        
        # Assertions
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_audit_publisher_instance.publish_certificate_generated.assert_called_once_with(
            "admin123", "user123", "/path/to/certificate.pdf"
        )
        mock_notification_publisher_instance.publish_certificate_notification.assert_called_once_with(
            "user123", "/path/to/certificate.pdf"
        )

    @patch('audit.service.audit_service.get_audit_publisher')
    def test_log_system_error_success(self, mock_audit_publisher, mock_db):
        """Test de journalisation d'erreur système"""
        # Mock setup
        mock_audit_publisher_instance = Mock()
        mock_audit_publisher.return_value = mock_audit_publisher_instance
        mock_audit_publisher_instance.publish_system_error.return_value = True
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Test
        result = AuditService.log_system_error(
            db=mock_db,
            error_type="DatabaseError",
            error_message="Connection failed",
            stack_trace="stack trace"
        )
        
        # Assertions
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_audit_publisher_instance.publish_system_error.assert_called_once_with(
            "DatabaseError", "Connection failed", "stack trace"
        )

    def test_get_audit_event_by_id_success(self, mock_db, sample_audit_event):
        """Test de récupération d'événement d'audit par ID"""
        # Mock setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_audit_event
        
        # Test
        result = AuditService.get_audit_event_by_id(mock_db, 1)
        
        # Assertions
        assert result == sample_audit_event
        mock_db.query.assert_called_once_with(AuditEvent)

    def test_get_audit_event_by_id_not_found(self, mock_db):
        """Test de récupération d'événement d'audit inexistant"""
        # Mock setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Test
        result = AuditService.get_audit_event_by_id(mock_db, 999)
        
        # Assertions
        assert result is None

    def test_get_audit_events_with_filters(self, mock_db):
        """Test de récupération d'événements d'audit avec filtres"""
        # Mock setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Test
        result = AuditService.get_audit_events(
            db=mock_db,
            skip=0,
            limit=10,
            user_id="user123",
            action="create",
            resource_type="shareholder",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow()
        )
        
        # Assertions
        assert result == []
        mock_db.query.assert_called_once_with(AuditEvent)

    def test_get_user_audit_events(self, mock_db):
        """Test de récupération d'événements d'audit d'un utilisateur"""
        # Mock setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Test
        result = AuditService.get_user_audit_events(mock_db, "user123", skip=0, limit=10)
        
        # Assertions
        assert result == []

    def test_get_resource_audit_events(self, mock_db):
        """Test de récupération d'événements d'audit d'une ressource"""
        # Mock setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Test
        result = AuditService.get_resource_audit_events(mock_db, "shareholder", "shareholder123", skip=0, limit=10)
        
        # Assertions
        assert result == []

    def test_get_audit_summary_success(self, mock_db):
        """Test de récupération du résumé d'audit"""
        # Mock setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.first.return_value = (100, 5, 3, datetime.utcnow())
        
        # Test
        result = AuditService.get_audit_summary(mock_db, user_id="user123")
        
        # Assertions
        assert isinstance(result, AuditEventSummary)
        assert result.total_events == 100
        assert result.unique_users == 5
        assert result.resource_types == 3

    def test_get_audit_summary_no_data(self, mock_db):
        """Test de récupération du résumé d'audit sans données"""
        # Mock setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.with_entities.return_value = mock_query
        mock_query.first.return_value = None
        
        # Test
        result = AuditService.get_audit_summary(mock_db)
        
        # Assertions
        assert isinstance(result, AuditEventSummary)
        assert result.total_events == 0
        assert result.unique_users == 0
        assert result.resource_types == 0

    def test_get_audit_statistics_success(self, mock_db):
        """Test de récupération des statistiques d'audit"""
        # Mock setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            ("create", 50),
            ("update", 30),
            ("delete", 10)
        ]
        
        # Test
        result = AuditService.get_audit_statistics(mock_db)
        
        # Assertions
        assert isinstance(result, dict)
        assert "action_statistics" in result
        assert "resource_statistics" in result
        assert "top_users" in result

    def test_search_audit_events_success(self, mock_db):
        """Test de recherche dans les événements d'audit"""
        # Mock setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Test
        result = AuditService.search_audit_events(mock_db, "test", skip=0, limit=10)
        
        # Assertions
        assert result == []

    def test_export_audit_events_json(self, mock_db):
        """Test d'export d'événements d'audit en JSON"""
        # Mock setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Test
        result = AuditService.export_audit_events(mock_db, format="json")
        
        # Assertions
        assert isinstance(result, str)
        assert result.startswith("[")

    def test_export_audit_events_csv(self, mock_db):
        """Test d'export d'événements d'audit en CSV"""
        # Mock setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # Test
        result = AuditService.export_audit_events(mock_db, format="csv")
        
        # Assertions
        assert isinstance(result, str)
        assert "ID,User ID,Action" in result

    def test_export_audit_events_invalid_format(self, mock_db):
        """Test d'export d'événements d'audit avec format invalide"""
        # Test
        with pytest.raises(ValueError):
            AuditService.export_audit_events(mock_db, format="invalid")

    def test_cleanup_old_audit_events_success(self, mock_db):
        """Test de nettoyage des anciens événements d'audit"""
        # Mock setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 50
        
        mock_db.commit = Mock()
        
        # Test
        result = AuditService.cleanup_old_audit_events(mock_db, days_to_keep=365)
        
        # Assertions
        assert result == 50
        mock_db.commit.assert_called_once()

    def test_cleanup_old_audit_events_error(self, mock_db):
        """Test de nettoyage des anciens événements d'audit avec erreur"""
        # Mock setup
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.delete.side_effect = SQLAlchemyError("Database error")
        
        mock_db.rollback = Mock()
        
        # Test
        result = AuditService.cleanup_old_audit_events(mock_db, days_to_keep=365)
        
        # Assertions
        assert result == 0
        mock_db.rollback.assert_called_once()


