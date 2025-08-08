"""
Configuration pour les tests de performance
"""
import pytest
import time
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.database import Base, get_db


@pytest.fixture(scope="session")
def performance_engine():
    """Moteur de base de données pour les tests de performance"""
    database_url = "postgresql://postgres:postgres@localhost:5432/corporate_os_performance"
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def performance_session(performance_engine):
    """Session de base de données pour les tests de performance"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=performance_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def performance_client(performance_session):
    """Client de test pour les tests de performance"""
    def override_get_db():
        try:
            yield performance_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def benchmark_data():
    """Données de test pour les benchmarks"""
    return {
        "shareholders": [
            {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "first_name": f"User{i}",
                "last_name": "Test",
                "company_name": f"Company{i}",
                "phone": f"+123456789{i:02d}"
            }
            for i in range(100)
        ],
        "issuances": [
            {
                "shareholder_id": f"550e8400-e29b-41d4-a716-446655440{i:03d}",
                "number_of_shares": 100 + i,
                "price_per_share": 10.50 + (i * 0.1),
                "total_amount": (100 + i) * (10.50 + (i * 0.1)),
                "issue_date": "2024-01-01T00:00:00"
            }
            for i in range(50)
        ]
    }


# Marqueurs pour les tests de performance
pytest_benchmark_plugin = pytest.importorskip("pytest_benchmark")


@pytest.fixture
def benchmark(benchmark):
    """Fixture pour les benchmarks"""
    return benchmark


# Utilitaires pour les tests de performance
class PerformanceTimer:
    """Classe utilitaire pour mesurer les performances"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
    
    @property
    def duration(self):
        """Durée en secondes"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def duration_ms(self):
        """Durée en millisecondes"""
        duration = self.duration
        return duration * 1000 if duration else None


@pytest.fixture
def timer():
    """Fixture pour le timer de performance"""
    return PerformanceTimer()

