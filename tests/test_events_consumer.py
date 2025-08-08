"""
Tests unitaires pour les consumers d'événements
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from events.consumer import (
    BaseEventHandler,
    AuditEventHandler,
    NotificationEventHandler,
    SystemEventHandler,
    EventConsumer,
    get_consumer,
    start_consumer
)
from core.event_type import EventTypeEnum


class TestBaseEventHandler:
    """Tests pour la classe de base BaseEventHandler"""

    def test_base_handler_abstract(self):
        """Test que BaseEventHandler est une classe abstraite"""
        with pytest.raises(TypeError):
            BaseEventHandler()


class TestAuditEventHandler:
    """Tests pour AuditEventHandler"""

    @pytest.fixture
    def audit_handler(self):
        """Fixture pour un handler d'audit"""
        return AuditEventHandler()

    def test_handle_user_login_success(self, audit_handler):
        """Test de traitement d'événement de connexion utilisateur"""
        payload = {
            "user_id": "user123",
            "user_email": "user@example.com",
            "user_role": "admin",
            "ip_address": "192.168.1.1"
        }
        event_id = "test-event-123"
        
        result = audit_handler.handle_user_login(payload, event_id)
        
        assert result is True

    def test_handle_user_login_failure(self, audit_handler):
        """Test de traitement d'événement de connexion avec erreur"""
        payload = {
            "user_id": "user123",
            "user_email": "user@example.com",
            "user_role": "admin",
            "ip_address": "192.168.1.1"
        }
        event_id = "test-event-123"
        
        # Simuler une erreur en modifiant le payload
        payload["invalid_key"] = None
        
        result = audit_handler.handle_user_login(payload, event_id)
        
        assert result is True  # Le handler gère les erreurs gracieusement

    def test_handle_user_logout_success(self, audit_handler):
        """Test de traitement d'événement de déconnexion utilisateur"""
        payload = {
            "user_id": "user123",
            "user_email": "user@example.com",
            "session_duration": 3600
        }
        event_id = "test-event-123"
        
        result = audit_handler.handle_user_logout(payload, event_id)
        
        assert result is True

    def test_handle_shareholder_created_success(self, audit_handler):
        """Test de traitement d'événement de création d'actionnaire"""
        payload = {
            "user_id": "admin123",
            "shareholder_data": {
                "id": "123",
                "username": "john.doe",
                "email": "john@example.com"
            }
        }
        event_id = "test-event-123"
        
        result = audit_handler.handle_shareholder_created(payload, event_id)
        
        assert result is True

    def test_handle_shareholder_updated_success(self, audit_handler):
        """Test de traitement d'événement de mise à jour d'actionnaire"""
        payload = {
            "user_id": "admin123",
            "shareholder_id": "123",
            "previous_data": {"username": "john.doe"},
            "new_data": {"username": "john.smith"}
        }
        event_id = "test-event-123"
        
        result = audit_handler.handle_shareholder_updated(payload, event_id)
        
        assert result is True

    def test_handle_share_issued_success(self, audit_handler):
        """Test de traitement d'événement d'émission d'actions"""
        payload = {
            "user_id": "admin123",
            "shareholder_id": "user123",
            "share_data": {
                "id": "456",
                "number_of_shares": 100,
                "price_per_share": 10.0
            }
        }
        event_id = "test-event-123"
        
        result = audit_handler.handle_share_issued(payload, event_id)
        
        assert result is True

    def test_handle_certificate_generated_success(self, audit_handler):
        """Test de traitement d'événement de génération de certificat"""
        payload = {
            "user_id": "admin123",
            "shareholder_id": "user123",
            "certificate_path": "/path/to/certificate.pdf"
        }
        event_id = "test-event-123"
        
        result = audit_handler.handle_certificate_generated(payload, event_id)
        
        assert result is True

    def test_handle_permission_changed_success(self, audit_handler):
        """Test de traitement d'événement de changement de permission"""
        payload = {
            "admin_user_id": "admin123",
            "target_user_id": "user123",
            "old_role": "actionnaire",
            "new_role": "admin"
        }
        event_id = "test-event-123"
        
        result = audit_handler.handle_permission_changed(payload, event_id)
        
        assert result is True

    def test_handle_data_export_success(self, audit_handler):
        """Test de traitement d'événement d'export de données"""
        payload = {
            "user_id": "admin123",
            "export_type": "audit_events",
            "export_format": "json",
            "record_count": 150
        }
        event_id = "test-event-123"
        
        result = audit_handler.handle_data_export(payload, event_id)
        
        assert result is True

    def test_handle_system_error_success(self, audit_handler):
        """Test de traitement d'événement d'erreur système"""
        payload = {
            "error_type": "DatabaseError",
            "error_message": "Connection failed",
            "stack_trace": "stack trace"
        }
        event_id = "test-event-123"
        
        result = audit_handler.handle_system_error(payload, event_id)
        
        assert result is True

    def test_handle_unknown_event_type(self, audit_handler):
        """Test de traitement d'un type d'événement inconnu"""
        payload = {
            "event_type": "unknown_event"
        }
        event_id = "test-event-123"
        
        result = audit_handler.handle(payload, event_id)
        
        assert result is False

    def test_handle_all_event_types(self, audit_handler):
        """Test de traitement de tous les types d'événements"""
        event_types = [
            EventTypeEnum.USER_LOGIN.value,
            EventTypeEnum.USER_LOGOUT.value,
            EventTypeEnum.SHAREHOLDER_CREATED.value,
            EventTypeEnum.SHAREHOLDER_UPDATED.value,
            EventTypeEnum.SHARE_ISSUED.value,
            EventTypeEnum.CERTIFICATE_GENERATED.value,
            EventTypeEnum.PERMISSION_CHANGED.value,
            EventTypeEnum.DATA_EXPORT.value,
            EventTypeEnum.SYSTEM_ERROR.value
        ]
        
        for event_type in event_types:
            payload = {"event_type": event_type}
            result = audit_handler.handle(payload, "test-event")
            assert result is True


class TestNotificationEventHandler:
    """Tests pour NotificationEventHandler"""

    @pytest.fixture
    def notification_handler(self):
        """Fixture pour un handler de notifications"""
        return NotificationEventHandler()

    def test_handle_share_issuance_notification_success(self, notification_handler):
        """Test de traitement de notification d'émission d'actions"""
        payload = {
            "user_id": "user123",
            "notification_type": "share_issuance",
            "title": "Nouvelle émission d'actions",
            "message": "Une émission de 100 actions a été créée",
            "metadata": {
                "shareholder_name": "John Doe",
                "share_count": 100,
                "total_amount": 10000.0
            }
        }
        event_id = "test-event-123"
        
        result = notification_handler.handle_share_issuance_notification(payload, event_id)
        
        assert result is True

    def test_handle_certificate_notification_success(self, notification_handler):
        """Test de traitement de notification de certificat"""
        payload = {
            "user_id": "user123",
            "notification_type": "certificate_generated",
            "title": "Certificat d'actions généré",
            "message": "Votre certificat d'actions a été généré",
            "metadata": {
                "certificate_path": "/path/to/certificate.pdf"
            }
        }
        event_id = "test-event-123"
        
        result = notification_handler.handle_certificate_notification(payload, event_id)
        
        assert result is True

    def test_handle_system_alert_success(self, notification_handler):
        """Test de traitement d'alerte système"""
        payload = {
            "user_id": "user123",
            "notification_type": "system_alert",
            "title": "Alerte système - DatabaseError",
            "message": "Connection to database failed",
            "metadata": {
                "alert_type": "DatabaseError"
            }
        }
        event_id = "test-event-123"
        
        result = notification_handler.handle_system_alert(payload, event_id)
        
        assert result is True

    def test_handle_unknown_notification_type(self, notification_handler):
        """Test de traitement d'un type de notification inconnu"""
        payload = {
            "notification_type": "unknown_notification"
        }
        event_id = "test-event-123"
        
        result = notification_handler.handle(payload, event_id)
        
        assert result is False


class TestSystemEventHandler:
    """Tests pour SystemEventHandler"""

    @pytest.fixture
    def system_handler(self):
        """Fixture pour un handler système"""
        return SystemEventHandler()

    def test_handle_application_startup_success(self, system_handler):
        """Test de traitement d'événement de démarrage d'application"""
        payload = {
            "event": "application_startup",
            "version": "1.0.0",
            "environment": "development"
        }
        event_id = "test-event-123"
        
        result = system_handler.handle_application_startup(payload, event_id)
        
        assert result is True

    def test_handle_database_backup_success(self, system_handler):
        """Test de traitement d'événement de sauvegarde de base de données"""
        payload = {
            "event": "database_backup",
            "backup_path": "/backup/db.sql",
            "backup_size": 1024000
        }
        event_id = "test-event-123"
        
        result = system_handler.handle_database_backup(payload, event_id)
        
        assert result is True

    def test_handle_unknown_system_event(self, system_handler):
        """Test de traitement d'un type d'événement système inconnu"""
        payload = {
            "event": "unknown_event"
        }
        event_id = "test-event-123"
        
        result = system_handler.handle(payload, event_id)
        
        assert result is False


class TestEventConsumer:
    """Tests pour EventConsumer"""

    @pytest.fixture
    def event_consumer(self):
        """Fixture pour un consumer d'événements"""
        return EventConsumer(host='test-host', port=5672, username='test', password='test')

    def test_event_consumer_init(self, event_consumer):
        """Test de l'initialisation du consumer"""
        assert event_consumer.host == 'test-host'
        assert event_consumer.port == 5672
        assert event_consumer.username == 'test'
        assert event_consumer.password == 'test'
        assert event_consumer.connection is None
        assert event_consumer.channel is None
        assert event_consumer.running is False
        
        # Vérifier que les handlers sont initialisés
        assert isinstance(event_consumer.audit_handler, AuditEventHandler)
        assert isinstance(event_consumer.notification_handler, NotificationEventHandler)
        assert isinstance(event_consumer.system_handler, SystemEventHandler)

    @patch('pika.BlockingConnection')
    @patch('pika.PlainCredentials')
    @patch('pika.ConnectionParameters')
    def test_connect_success(self, mock_connection_params, mock_credentials, mock_connection, event_consumer):
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
        event_consumer.connect()
        
        # Assertions
        mock_credentials.assert_called_once_with('test', 'test')
        mock_connection_params.assert_called_once()
        mock_connection.assert_called_once_with(mock_params_instance)
        assert event_consumer.connection == mock_connection_instance
        assert event_consumer.channel == mock_channel

    def test_callback_audit_event_success(self, event_consumer):
        """Test de callback pour un événement d'audit"""
        # Mock setup
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 123
        
        mock_properties = Mock()
        
        message = {
            "event_id": "test-event-123",
            "event_type": EventTypeEnum.USER_LOGIN.value,
            "payload": {
                "user_id": "user123",
                "user_email": "user@example.com",
                "user_role": "admin"
            }
        }
        body = json.dumps(message).encode('utf-8')
        
        # Test
        event_consumer.callback(mock_channel, mock_method, mock_properties, body)
        
        # Assertions
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)

    def test_callback_notification_event_success(self, event_consumer):
        """Test de callback pour un événement de notification"""
        # Mock setup
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 123
        
        mock_properties = Mock()
        
        message = {
            "event_id": "test-event-123",
            "event_type": "notification",
            "payload": {
                "user_id": "user123",
                "notification_type": "share_issuance",
                "title": "Test",
                "message": "Test message"
            }
        }
        body = json.dumps(message).encode('utf-8')
        
        # Test
        event_consumer.callback(mock_channel, mock_method, mock_properties, body)
        
        # Assertions
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)

    def test_callback_system_event_success(self, event_consumer):
        """Test de callback pour un événement système"""
        # Mock setup
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 123
        
        mock_properties = Mock()
        
        message = {
            "event_id": "test-event-123",
            "event_type": "system",
            "payload": {
                "event": "application_startup",
                "version": "1.0.0"
            }
        }
        body = json.dumps(message).encode('utf-8')
        
        # Test
        event_consumer.callback(mock_channel, mock_method, mock_properties, body)
        
        # Assertions
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)

    def test_callback_unknown_event_type(self, event_consumer):
        """Test de callback pour un type d'événement inconnu"""
        # Mock setup
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 123
        
        mock_properties = Mock()
        
        message = {
            "event_id": "test-event-123",
            "event_type": "unknown_event",
            "payload": {}
        }
        body = json.dumps(message).encode('utf-8')
        
        # Test
        event_consumer.callback(mock_channel, mock_method, mock_properties, body)
        
        # Assertions
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)

    def test_callback_json_decode_error(self, event_consumer):
        """Test de callback avec erreur de décodage JSON"""
        # Mock setup
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 123
        
        mock_properties = Mock()
        
        # Body JSON invalide
        body = b"invalid json"
        
        # Test
        event_consumer.callback(mock_channel, mock_method, mock_properties, body)
        
        # Assertions
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)

    def test_callback_handler_exception(self, event_consumer):
        """Test de callback avec exception dans le handler"""
        # Mock setup
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 123
        
        mock_properties = Mock()
        
        message = {
            "event_id": "test-event-123",
            "event_type": EventTypeEnum.USER_LOGIN.value,
            "payload": {
                "user_id": "user123",
                "user_email": "user@example.com",
                "user_role": "admin"
            }
        }
        body = json.dumps(message).encode('utf-8')
        
        # Mock une exception dans le handler
        event_consumer.audit_handler.handle_user_login = Mock(side_effect=Exception("Handler error"))
        
        # Test
        event_consumer.callback(mock_channel, mock_method, mock_properties, body)
        
        # Assertions
        mock_channel.basic_nack.assert_called_once_with(delivery_tag=123, requeue=True)

    def test_disconnect_success(self, event_consumer):
        """Test de déconnexion réussie"""
        # Mock connection
        mock_connection = Mock()
        mock_connection.is_closed = False
        event_consumer.connection = mock_connection
        event_consumer.running = True
        
        event_consumer.disconnect()
        
        assert event_consumer.running is False
        mock_connection.close.assert_called_once()

    @patch('pika.BlockingConnection')
    def test_start_consuming_success(self, mock_connection, event_consumer):
        """Test de démarrage de la consommation"""
        # Mock setup
        mock_connection_instance = Mock()
        mock_connection.return_value = mock_connection_instance
        mock_connection_instance.is_closed = False
        
        mock_channel = Mock()
        mock_connection_instance.channel.return_value = mock_channel
        
        event_consumer.connection = mock_connection_instance
        event_consumer.channel = mock_channel
        
        # Mock start_consuming pour éviter la boucle infinie
        mock_channel.start_consuming.side_effect = KeyboardInterrupt()
        
        # Test
        event_consumer.start_consuming('test_queue')
        
        # Assertions
        mock_channel.basic_consume.assert_called_once()
        mock_channel.start_consuming.assert_called_once()


class TestConsumerFactories:
    """Tests pour les fonctions factory des consumers"""

    def test_get_consumer_singleton(self):
        """Test que get_consumer retourne toujours la même instance"""
        consumer1 = get_consumer()
        consumer2 = get_consumer()
        
        assert consumer1 is consumer2
        assert isinstance(consumer1, EventConsumer)

    @patch('events.consumer.EventConsumer')
    def test_start_consumer(self, mock_consumer_class):
        """Test de la fonction start_consumer"""
        mock_consumer = Mock()
        mock_consumer_class.return_value = mock_consumer
        
        # Mock start_consuming pour éviter la boucle infinie
        mock_consumer.start_consuming.side_effect = KeyboardInterrupt()
        
        # Test
        with pytest.raises(KeyboardInterrupt):
            start_consumer('test_queue')
        
        mock_consumer.start_consuming.assert_called_once_with('test_queue')


