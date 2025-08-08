"""
Tests unitaires pour l'API d'audit
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from fastapi import HTTPException
from fastapi.testclient import TestClient

from audit.api.audit_api import router
from app.database.models import AuditEvent
from app.schemas.audit import AuditEventSummary, AuditEventStatistics
from core.event_type import EventTypeEnum


class TestAuditAPI:
    """Tests pour l'API d'audit"""

    @pytest.fixture
    def client(self):
        """Fixture pour un client de test"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.fixture
    def mock_db(self):
        """Fixture pour une session de base de données mockée"""
        return Mock()

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

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_get_audit_events_success(self, mock_get_db, mock_audit_service, client, mock_db, sample_audit_event):
        """Test de récupération réussie des événements d'audit"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.get_audit_events.return_value = [sample_audit_event]
        
        # Test
        response = client.get("/audit/events?skip=0&limit=10")
        
        # Assertions
        assert response.status_code == 200
        mock_audit_service.get_audit_events.assert_called_once()

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_get_audit_events_with_filters(self, mock_get_db, mock_audit_service, client, mock_db):
        """Test de récupération des événements d'audit avec filtres"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.get_audit_events.return_value = []
        
        # Test
        response = client.get("/audit/events?user_id=user123&action=create&resource_type=shareholder")
        
        # Assertions
        assert response.status_code == 200
        mock_audit_service.get_audit_events.assert_called_once()

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_get_audit_event_by_id_success(self, mock_get_db, mock_audit_service, client, mock_db, sample_audit_event):
        """Test de récupération réussie d'un événement d'audit par ID"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.get_audit_event_by_id.return_value = sample_audit_event
        
        # Test
        response = client.get("/audit/events/1")
        
        # Assertions
        assert response.status_code == 200
        mock_audit_service.get_audit_event_by_id.assert_called_once_with(mock_db, 1)

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_get_audit_event_by_id_not_found(self, mock_get_db, mock_audit_service, client, mock_db):
        """Test de récupération d'un événement d'audit inexistant"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.get_audit_event_by_id.return_value = None
        
        # Test
        response = client.get("/audit/events/999")
        
        # Assertions
        assert response.status_code == 404
        assert "Événement d'audit non trouvé" in response.json()["detail"]

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_get_user_audit_events_success(self, mock_get_db, mock_audit_service, client, mock_db, sample_audit_event):
        """Test de récupération réussie des événements d'audit d'un utilisateur"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.get_user_audit_events.return_value = [sample_audit_event]
        
        # Test
        response = client.get("/audit/events/user/user123?skip=0&limit=10")
        
        # Assertions
        assert response.status_code == 200
        mock_audit_service.get_user_audit_events.assert_called_once_with(mock_db, "user123", 0, 10)

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_get_resource_audit_events_success(self, mock_get_db, mock_audit_service, client, mock_db, sample_audit_event):
        """Test de récupération réussie des événements d'audit d'une ressource"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.get_resource_audit_events.return_value = [sample_audit_event]
        
        # Test
        response = client.get("/audit/events/resource/shareholder/shareholder123?skip=0&limit=10")
        
        # Assertions
        assert response.status_code == 200
        mock_audit_service.get_resource_audit_events.assert_called_once_with(mock_db, "shareholder", "shareholder123", 0, 10)

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_get_audit_summary_success(self, mock_get_db, mock_audit_service, client, mock_db):
        """Test de récupération réussie du résumé d'audit"""
        # Mock setup
        mock_get_db.return_value = mock_db
        summary = AuditEventSummary(
            total_events=100,
            unique_users=5,
            resource_types=3,
            last_event_date=datetime.utcnow()
        )
        mock_audit_service.get_audit_summary.return_value = summary
        
        # Test
        response = client.get("/audit/summary")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 100
        assert data["unique_users"] == 5
        assert data["resource_types"] == 3

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_get_audit_summary_error(self, mock_get_db, mock_audit_service, client, mock_db):
        """Test de récupération du résumé d'audit avec erreur"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.get_audit_summary.return_value = None
        
        # Test
        response = client.get("/audit/summary")
        
        # Assertions
        assert response.status_code == 500
        assert "Erreur lors de la récupération du résumé d'audit" in response.json()["detail"]

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_get_audit_statistics_success(self, mock_get_db, mock_audit_service, client, mock_db):
        """Test de récupération réussie des statistiques d'audit"""
        # Mock setup
        mock_get_db.return_value = mock_db
        statistics = {
            "action_statistics": [
                {"action": "create", "count": 50},
                {"action": "update", "count": 30}
            ],
            "resource_statistics": [
                {"resource_type": "shareholder", "count": 60}
            ],
            "top_users": [
                {"user_id": "admin", "count": 80}
            ]
        }
        mock_audit_service.get_audit_statistics.return_value = statistics
        
        # Test
        response = client.get("/audit/statistics")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "action_statistics" in data
        assert "resource_statistics" in data
        assert "top_users" in data

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_search_audit_events_success(self, mock_get_db, mock_audit_service, client, mock_db, sample_audit_event):
        """Test de recherche réussie dans les événements d'audit"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.search_audit_events.return_value = [sample_audit_event]
        
        # Test
        response = client.get("/audit/search?q=test&skip=0&limit=10")
        
        # Assertions
        assert response.status_code == 200
        mock_audit_service.search_audit_events.assert_called_once_with(mock_db, "test", 0, 10)

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_export_audit_events_json_success(self, mock_get_db, mock_audit_service, client, mock_db):
        """Test d'export réussi des événements d'audit en JSON"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.export_audit_events.return_value = '[]'
        
        # Test
        response = client.get("/audit/export?format=json")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_export_audit_events_csv_success(self, mock_get_db, mock_audit_service, client, mock_db):
        """Test d'export réussi des événements d'audit en CSV"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.export_audit_events.return_value = "ID,User ID,Action\n1,user123,create"
        
        # Test
        response = client.get("/audit/export?format=csv")
        
        # Assertions
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert "ID,User ID,Action" in response.text

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_export_audit_events_invalid_format(self, mock_get_db, mock_audit_service, client, mock_db):
        """Test d'export avec format invalide"""
        # Mock setup
        mock_get_db.return_value = mock_db
        
        # Test
        response = client.get("/audit/export?format=invalid")
        
        # Assertions
        assert response.status_code == 400
        assert "Format d'export non supporté" in response.json()["detail"]

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_cleanup_old_audit_events_success(self, mock_get_db, mock_audit_service, client, mock_db):
        """Test de nettoyage réussi des anciens événements d'audit"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.cleanup_old_audit_events.return_value = 50
        
        # Test
        response = client.post("/audit/cleanup?days_to_keep=365")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 50
        assert "50 anciens événements d'audit supprimés" in data["message"]

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_cleanup_old_audit_events_with_custom_days(self, mock_get_db, mock_audit_service, client, mock_db):
        """Test de nettoyage avec nombre de jours personnalisé"""
        # Mock setup
        mock_get_db.return_value = mock_db
        mock_audit_service.cleanup_old_audit_events.return_value = 25
        
        # Test
        response = client.post("/audit/cleanup?days_to_keep=180")
        
        # Assertions
        assert response.status_code == 200
        mock_audit_service.cleanup_old_audit_events.assert_called_once_with(mock_db, 180)


class TestAuditAPIIntegration:
    """Tests d'intégration pour l'API d'audit"""

    @pytest.fixture
    def client(self):
        """Fixture pour un client de test avec authentification mockée"""
        from fastapi import FastAPI, Depends
        from fastapi.security import HTTPBearer
        
        app = FastAPI()
        
        # Mock authentication dependency
        def mock_auth():
            return {"sub": "admin", "realm_access": {"roles": ["admin"]}}
        
        app.dependency_overrides[mock_auth] = mock_auth
        app.include_router(router)
        
        return TestClient(app)

    @patch('audit.api.audit_api.AuditService')
    @patch('audit.api.audit_api.get_db')
    def test_full_audit_workflow(self, mock_get_db, mock_audit_service, client, mock_db):
        """Test du workflow complet d'audit"""
        # Mock setup
        mock_get_db.return_value = mock_db
        
        # Mock pour get_audit_events
        mock_audit_service.get_audit_events.return_value = []
        
        # Mock pour get_audit_summary
        summary = AuditEventSummary(
            total_events=100,
            unique_users=5,
            resource_types=3,
            last_event_date=datetime.utcnow()
        )
        mock_audit_service.get_audit_summary.return_value = summary
        
        # Mock pour get_audit_statistics
        statistics = {
            "action_statistics": [{"action": "create", "count": 50}],
            "resource_statistics": [{"resource_type": "shareholder", "count": 60}],
            "top_users": [{"user_id": "admin", "count": 80}]
        }
        mock_audit_service.get_audit_statistics.return_value = statistics
        
        # Test 1: Récupération des événements
        response1 = client.get("/audit/events?skip=0&limit=10")
        assert response1.status_code == 200
        
        # Test 2: Récupération du résumé
        response2 = client.get("/audit/summary")
        assert response2.status_code == 200
        assert response2.json()["total_events"] == 100
        
        # Test 3: Récupération des statistiques
        response3 = client.get("/audit/statistics")
        assert response3.status_code == 200
        assert "action_statistics" in response3.json()
        
        # Test 4: Recherche
        response4 = client.get("/audit/search?q=test")
        assert response4.status_code == 200
        
        # Test 5: Export
        response5 = client.get("/audit/export?format=json")
        assert response5.status_code == 200


