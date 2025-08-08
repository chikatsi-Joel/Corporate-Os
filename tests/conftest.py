"""
Configuration pytest pour les tests de Corporate OS
"""
import pytest
import asyncio
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.database.database import Base, get_db
from app.main import app
from app.database.models import ShareholderProfile, ShareIssuance, AuditEvent
from app.core.config import settings


# Configuration des tests
@pytest.fixture(scope="session")
def event_loop():
    """Créer une boucle d'événements pour les tests asynchrones"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_database_url():
    """URL de la base de données de test"""
    return "postgresql://postgres:postgres@localhost:5432/corporate_os_test"


@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """Moteur de base de données de test"""
    engine = create_engine(test_database_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_session(test_engine) -> Generator[Session, None, None]:
    """Session de base de données de test"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(test_session) -> Generator[TestClient, None, None]:
    """Client de test FastAPI"""
    def override_get_db():
        try:
            yield test_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Fixtures pour les données de test
@pytest.fixture
def sample_shareholder_profile() -> Dict[str, Any]:
    """Profil d'actionnaire de test"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "keycloak_id": "test-keycloak-id",
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "company_name": "Test Company",
        "phone": "+1234567890"
    }


@pytest.fixture
def sample_share_issuance() -> Dict[str, Any]:
    """Émission d'actions de test"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "shareholder_id": "550e8400-e29b-41d4-a716-446655440000",
        "number_of_shares": 100,
        "price_per_share": 10.50,
        "total_amount": 1050.00,
        "issue_date": "2024-01-01T00:00:00",
        "status": "issued"
    }


@pytest.fixture
def sample_audit_event() -> Dict[str, Any]:
    """Événement d'audit de test"""
    return {
        "id": 1,
        "event_type": "user.login",
        "event_id": "550e8400-e29b-41d4-a716-446655440002",
        "user_id": "testuser",
        "user_email": "test@example.com",
        "action": "login",
        "description": "Test login event",
        "status": "processed"
    }


# Fixtures pour les mocks
@pytest.fixture
def mock_keycloak():
    """Mock pour Keycloak"""
    with patch("app.core.auth.keycloak") as mock:
        mock.return_value = Mock()
        yield mock


@pytest.fixture
def mock_event_bus():
    """Mock pour le bus d'événements"""
    with patch("app.core.events.event_bus") as mock:
        mock.publish = Mock()
        yield mock


@pytest.fixture
def mock_certificate_service():
    """Mock pour le service de certificats"""
    with patch("app.services.certificate_service.CertificateService") as mock:
        mock.generate_certificate.return_value = "/path/to/certificate.pdf"
        yield mock


# Fixtures pour les utilisateurs de test
@pytest.fixture
def admin_user() -> Dict[str, Any]:
    """Utilisateur admin de test"""
    return {
        "sub": "admin-user-id",
        "preferred_username": "admin",
        "email": "admin@corporate-os.com",
        "given_name": "Admin",
        "family_name": "User",
        "realm_access": {
            "roles": ["admin"]
        }
    }


@pytest.fixture
def actionnaire_user() -> Dict[str, Any]:
    """Utilisateur actionnaire de test"""
    return {
        "sub": "actionnaire-user-id",
        "preferred_username": "actionnaire",
        "email": "actionnaire@corporate-os.com",
        "given_name": "Actionnaire",
        "family_name": "User",
        "realm_access": {
            "roles": ["actionnaire"]
        }
    }


@pytest.fixture
def user_without_roles() -> Dict[str, Any]:
    """Utilisateur sans rôles de test"""
    return {
        "sub": "no-role-user-id",
        "preferred_username": "norole",
        "email": "norole@corporate-os.com",
        "given_name": "No",
        "family_name": "Role",
        "realm_access": {
            "roles": []
        }
    }


# Fixtures pour les tests d'API
@pytest.fixture
def auth_headers_admin(admin_user):
    """Headers d'authentification pour admin"""
    return {
        "Authorization": f"Bearer mock-token-admin",
        "Content-Type": "application/json"
    }


@pytest.fixture
def auth_headers_actionnaire(actionnaire_user):
    """Headers d'authentification pour actionnaire"""
    return {
        "Authorization": f"Bearer mock-token-actionnaire",
        "Content-Type": "application/json"
    }


# Configuration des marqueurs
def pytest_configure(config):
    """Configuration des marqueurs pytest"""
    config.addinivalue_line(
        "markers", "unit: Tests unitaires"
    )
    config.addinivalue_line(
        "markers", "integration: Tests d'intégration"
    )
    config.addinivalue_line(
        "markers", "slow: Tests lents"
    )
    config.addinivalue_line(
        "markers", "security: Tests de sécurité"
    )
    config.addinivalue_line(
        "markers", "performance: Tests de performance"
    )
    config.addinivalue_line(
        "markers", "api: Tests d'API"
    )
    config.addinivalue_line(
        "markers", "database: Tests de base de données"
    )
    config.addinivalue_line(
        "markers", "auth: Tests d'authentification"
    )
    config.addinivalue_line(
        "markers", "audit: Tests d'audit"
    )
    config.addinivalue_line(
        "markers", "events: Tests d'événements"
    )


# Configuration des timeouts
@pytest.fixture(autouse=True)
def timeout_setup():
    """Configuration automatique des timeouts"""
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Test timeout")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5 minutes timeout
    
    yield
    
    signal.alarm(0)

