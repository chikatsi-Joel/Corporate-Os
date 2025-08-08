"""
Tests unitaires pour les publishers d'événements
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from events.publisher import (
    BasePublisher,
    AuditEventPublisher,
    NotificationEventPublisher,
    SystemEventPublisher,
    get_audit_publisher,
    get_notification_publisher,
    get_system_publisher
)
from core.event_type import EventTypeEnum


class TestBasePublisher:
    """Tests pour la classe de base BasePublisher"""

    @pytest.fixture
    def base_publisher(self):
        """Fixture pour un publisher de base"""
        return BasePublisher(host='test-host', port=5672, username='test', password='test')

    def test_base_publisher_init(self, base_publisher):
        """Test de l'initialisation du publisher de base"""
        assert base_publisher.host == 'test-host'
        assert base_publisher.port == 5672
        assert base_publisher.username == 'test'
        assert base_publisher.password == 'test'
        assert base_publisher.connection is None
        assert base_publisher.channel is None

    @patch('pika.BlockingConnection')
    @patch('pika.PlainCredentials')
    @patch('pika.ConnectionParameters')
    def test_connect_success(self, mock_connection_params, mock_credentials, mock_connection, base_publisher):
        """Test de connexion réussie"""
        # Mock setup
        mock_credentials_instance = Mock()
        mock_credentials.return_value = mock_credentials_instance
        
        mock_params_instance = Mock()
        mock_connection_params.return_value = mock_params_instance
        
        mock_connection_instance = Mock()
        mock_connection.return_value = mock_connection_instance
        
        mock_channel = Mock()
        mock_connection_instance.channel.return_value = mock_channel
        
        # Test
        base_publisher.connect()
        
        # Assertions
        mock_credentials.assert_called_once_with('test', 'test')
        mock_connection_params.assert_called_once()
        mock_connection.assert_called_once_with(mock_params_instance)
        assert base_publisher.connection == mock_connection_instance
        assert base_publisher.channel == mock_channel

    @patch('pika.BlockingConnection')
    def test_connect_failure(self, mock_connection, base_publisher):
        """Test de connexion échouée"""
        mock_connection.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception) as exc_info:
            base_publisher.connect()
        
        assert str(exc_info.value) == "Connection failed"

    def test_disconnect_success(self, base_publisher):
        """Test de déconnexion réussie"""
        # Mock connection
        mock_connection = Mock()
        mock_connection.is_closed = False
        base_publisher.connection = mock_connection
        
        base_publisher.disconnect()
        
        mock_connection.close.assert_called_once()

    def test_disconnect_no_connection(self, base_publisher):
        """Test de déconnexion sans connexion"""
        # Should not raise any exception
        base_publisher.disconnect()

    @patch('pika.BlockingConnection')
    def test_publish_message_success(self, mock_connection, base_publisher):
        """Test de publication de message réussie"""
        # Mock setup
        mock_connection_instance = Mock()
        mock_connection.return_value = mock_connection_instance
        mock_connection_instance.is_closed = False
        
        mock_channel = Mock()
        mock_connection_instance.channel.return_value = mock_channel
        base_publisher.connection = mock_connection_instance
        base_publisher.channel = mock_channel
        
        # Test
        message = {"test": "data"}
        result = base_publisher._publish_message(message, "test.routing.key")
        
        # Assertions
        assert result is True
        mock_channel.basic_publish.assert_called_once()

    @patch('pika.BlockingConnection')
    def test_publish_message_failure(self, mock_connection, base_publisher):
        """Test de publication de message échouée"""
        # Mock setup
        mock_connection_instance = Mock()
        mock_connection.return_value = mock_connection_instance
        mock_connection_instance.is_closed = False
        
        mock_channel = Mock()
        mock_channel.basic_publish.side_effect = Exception("Publish failed")
        mock_connection_instance.channel.return_value = mock_channel
        base_publisher.connection = mock_connection_instance
        base_publisher.channel = mock_channel
        
        # Test
        message = {"test": "data"}
        result = base_publisher._publish_message(message, "test.routing.key")
        
        # Assertions
        assert result is False


class TestAuditEventPublisher:
    """Tests pour AuditEventPublisher"""

    @pytest.fixture
    def audit_publisher(self):
        """Fixture pour un publisher d'audit"""
        return AuditEventPublisher()

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_user_login(self, mock_publish, audit_publisher):
        """Test de publication d'événement de connexion utilisateur"""
        mock_publish.return_value = True
        
        result = audit_publisher.publish_user_login(
            "user123", "user@example.com", "admin", "192.168.1.1", "Mozilla/5.0"
        )
        
        assert result is True
        mock_publish.assert_called_once()
        
        # Vérifier le contenu du message
        call_args = mock_publish.call_args
        message = call_args[0][0]
        routing_key = call_args[0][1]
        
        assert routing_key == "audit.user.login"
        assert message["event_type"] == EventTypeEnum.USER_LOGIN.value
        assert message["payload"]["user_id"] == "user123"
        assert message["payload"]["user_email"] == "user@example.com"
        assert message["payload"]["user_role"] == "admin"
        assert message["payload"]["ip_address"] == "192.168.1.1"
        assert message["payload"]["user_agent"] == "Mozilla/5.0"

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_user_logout(self, mock_publish, audit_publisher):
        """Test de publication d'événement de déconnexion utilisateur"""
        mock_publish.return_value = True
        
        result = audit_publisher.publish_user_logout("user123", "user@example.com", 3600)
        
        assert result is True
        mock_publish.assert_called_once()
        
        call_args = mock_publish.call_args
        message = call_args[0][0]
        routing_key = call_args[0][1]
        
        assert routing_key == "audit.user.logout"
        assert message["event_type"] == EventTypeEnum.USER_LOGOUT.value
        assert message["payload"]["user_id"] == "user123"
        assert message["payload"]["user_email"] == "user@example.com"
        assert message["payload"]["session_duration"] == 3600

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_shareholder_created(self, mock_publish, audit_publisher):
        """Test de publication d'événement de création d'actionnaire"""
        mock_publish.return_value = True
        
        shareholder_data = {"id": "123", "username": "john.doe", "email": "john@example.com"}
        result = audit_publisher.publish_shareholder_created("admin123", shareholder_data)
        
        assert result is True
        mock_publish.assert_called_once()
        
        call_args = mock_publish.call_args
        message = call_args[0][0]
        routing_key = call_args[0][1]
        
        assert routing_key == "audit.shareholder.created"
        assert message["event_type"] == EventTypeEnum.SHAREHOLDER_CREATED.value
        assert message["payload"]["user_id"] == "admin123"
        assert message["payload"]["shareholder_data"] == shareholder_data

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_share_issued(self, mock_publish, audit_publisher):
        """Test de publication d'événement d'émission d'actions"""
        mock_publish.return_value = True
        
        share_data = {"id": "456", "number_of_shares": 100, "price_per_share": 10.0}
        result = audit_publisher.publish_share_issued("admin123", "user123", share_data)
        
        assert result is True
        mock_publish.assert_called_once()
        
        call_args = mock_publish.call_args
        message = call_args[0][0]
        routing_key = call_args[0][1]
        
        assert routing_key == "audit.share.issued"
        assert message["event_type"] == EventTypeEnum.SHARE_ISSUED.value
        assert message["payload"]["user_id"] == "admin123"
        assert message["payload"]["shareholder_id"] == "user123"
        assert message["payload"]["share_data"] == share_data

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_certificate_generated(self, mock_publish, audit_publisher):
        """Test de publication d'événement de génération de certificat"""
        mock_publish.return_value = True
        
        result = audit_publisher.publish_certificate_generated("admin123", "user123", "/path/to/certificate.pdf")
        
        assert result is True
        mock_publish.assert_called_once()
        
        call_args = mock_publish.call_args
        message = call_args[0][0]
        routing_key = call_args[0][1]
        
        assert routing_key == "audit.certificate.generated"
        assert message["event_type"] == EventTypeEnum.CERTIFICATE_GENERATED.value
        assert message["payload"]["user_id"] == "admin123"
        assert message["payload"]["shareholder_id"] == "user123"
        assert message["payload"]["certificate_path"] == "/path/to/certificate.pdf"

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_system_error(self, mock_publish, audit_publisher):
        """Test de publication d'événement d'erreur système"""
        mock_publish.return_value = True
        
        result = audit_publisher.publish_system_error("DatabaseError", "Connection failed", "stack trace")
        
        assert result is True
        mock_publish.assert_called_once()
        
        call_args = mock_publish.call_args
        message = call_args[0][0]
        routing_key = call_args[0][1]
        
        assert routing_key == "audit.system.error"
        assert message["event_type"] == EventTypeEnum.SYSTEM_ERROR.value
        assert message["payload"]["error_type"] == "DatabaseError"
        assert message["payload"]["error_message"] == "Connection failed"
        assert message["payload"]["stack_trace"] == "stack trace"

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_generic_method(self, mock_publish, audit_publisher):
        """Test de la méthode générique publish"""
        mock_publish.return_value = True
        
        result = audit_publisher.publish(
            event_type=EventTypeEnum.USER_LOGIN.value,
            user_id="user123",
            user_email="user@example.com",
            user_role="admin"
        )
        
        assert result is True
        mock_publish.assert_called_once()

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_unknown_event_type(self, mock_publish, audit_publisher):
        """Test de publication d'un type d'événement inconnu"""
        mock_publish.return_value = True
        
        result = audit_publisher.publish(event_type="unknown_event")
        
        assert result is False
        mock_publish.assert_not_called()


class TestNotificationEventPublisher:
    """Tests pour NotificationEventPublisher"""

    @pytest.fixture
    def notification_publisher(self):
        """Fixture pour un publisher de notifications"""
        return NotificationEventPublisher()

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_share_issuance_notification(self, mock_publish, notification_publisher):
        """Test de publication de notification d'émission d'actions"""
        mock_publish.return_value = True
        
        result = notification_publisher.publish_share_issuance_notification(
            "user123", "John Doe", 100, 10000.0
        )
        
        assert result is True
        mock_publish.assert_called_once()
        
        call_args = mock_publish.call_args
        message = call_args[0][0]
        routing_key = call_args[0][1]
        
        assert routing_key == "notification.share.issuance"
        assert message["event_type"] == "notification"
        assert message["payload"]["user_id"] == "user123"
        assert message["payload"]["notification_type"] == "share_issuance"
        assert message["payload"]["title"] == "Nouvelle émission d'actions"
        assert "Une émission de 100 actions pour 10000.0€" in message["payload"]["message"]

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_certificate_notification(self, mock_publish, notification_publisher):
        """Test de publication de notification de certificat"""
        mock_publish.return_value = True
        
        result = notification_publisher.publish_certificate_notification(
            "user123", "/path/to/certificate.pdf"
        )
        
        assert result is True
        mock_publish.assert_called_once()
        
        call_args = mock_publish.call_args
        message = call_args[0][0]
        routing_key = call_args[0][1]
        
        assert routing_key == "notification.certificate.generated"
        assert message["event_type"] == "notification"
        assert message["payload"]["user_id"] == "user123"
        assert message["payload"]["notification_type"] == "certificate_generated"
        assert message["payload"]["title"] == "Certificat d'actions généré"

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_system_alert(self, mock_publish, notification_publisher):
        """Test de publication d'alerte système"""
        mock_publish.return_value = True
        
        result = notification_publisher.publish_system_alert(
            "user123", "DatabaseError", "Connection to database failed"
        )
        
        assert result is True
        mock_publish.assert_called_once()
        
        call_args = mock_publish.call_args
        message = call_args[0][0]
        routing_key = call_args[0][1]
        
        assert routing_key == "notification.system.alert"
        assert message["event_type"] == "notification"
        assert message["payload"]["user_id"] == "user123"
        assert message["payload"]["notification_type"] == "system_alert"
        assert message["payload"]["title"] == "Alerte système - DatabaseError"


class TestSystemEventPublisher:
    """Tests pour SystemEventPublisher"""

    @pytest.fixture
    def system_publisher(self):
        """Fixture pour un publisher système"""
        return SystemEventPublisher()

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_application_startup(self, mock_publish, system_publisher):
        """Test de publication d'événement de démarrage d'application"""
        mock_publish.return_value = True
        
        result = system_publisher.publish_application_startup("1.0.0", "development")
        
        assert result is True
        mock_publish.assert_called_once()
        
        call_args = mock_publish.call_args
        message = call_args[0][0]
        routing_key = call_args[0][1]
        
        assert routing_key == "system.application.startup"
        assert message["event_type"] == "system"
        assert message["payload"]["event"] == "application_startup"
        assert message["payload"]["version"] == "1.0.0"
        assert message["payload"]["environment"] == "development"

    @patch.object(BasePublisher, '_publish_message')
    def test_publish_database_backup(self, mock_publish, system_publisher):
        """Test de publication d'événement de sauvegarde de base de données"""
        mock_publish.return_value = True
        
        result = system_publisher.publish_database_backup("/backup/db.sql", 1024000)
        
        assert result is True
        mock_publish.assert_called_once()
        
        call_args = mock_publish.call_args
        message = call_args[0][0]
        routing_key = call_args[0][1]
        
        assert routing_key == "system.database.backup"
        assert message["event_type"] == "system"
        assert message["payload"]["event"] == "database_backup"
        assert message["payload"]["backup_path"] == "/backup/db.sql"
        assert message["payload"]["backup_size"] == 1024000


class TestPublisherFactories:
    """Tests pour les fonctions factory des publishers"""

    def test_get_audit_publisher_singleton(self):
        """Test que get_audit_publisher retourne toujours la même instance"""
        publisher1 = get_audit_publisher()
        publisher2 = get_audit_publisher()
        
        assert publisher1 is publisher2
        assert isinstance(publisher1, AuditEventPublisher)

    def test_get_notification_publisher_singleton(self):
        """Test que get_notification_publisher retourne toujours la même instance"""
        publisher1 = get_notification_publisher()
        publisher2 = get_notification_publisher()
        
        assert publisher1 is publisher2
        assert isinstance(publisher1, NotificationEventPublisher)

    def test_get_system_publisher_singleton(self):
        """Test que get_system_publisher retourne toujours la même instance"""
        publisher1 = get_system_publisher()
        publisher2 = get_system_publisher()
        
        assert publisher1 is publisher2
        assert isinstance(publisher1, SystemEventPublisher)


