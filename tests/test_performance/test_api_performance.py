"""
Tests de performance pour l'API Corporate OS
"""
import pytest
import time
from typing import List, Dict, Any
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.performance
class TestAPIPerformance:
    """Tests de performance pour l'API"""
    
    def test_health_check_performance(self, performance_client: TestClient, benchmark):
        """Test de performance pour l'endpoint de santé"""
        
        def health_check():
            response = performance_client.get("/health")
            assert response.status_code == 200
        
        # Benchmark de l'endpoint de santé
        result = benchmark(health_check)
        
        # Vérifications de performance
        assert result.stats.mean < 0.1  # Moins de 100ms en moyenne
        assert result.stats.max < 0.5   # Moins de 500ms au maximum
    
    def test_get_shareholders_performance(self, performance_client: TestClient, benchmark, benchmark_data):
        """Test de performance pour la récupération des actionnaires"""
        
        # Préparer les données de test
        shareholders = benchmark_data["shareholders"]
        
        def get_shareholders():
            response = performance_client.get("/api/shareholders/")
            assert response.status_code == 200
        
        # Benchmark de l'endpoint
        result = benchmark(get_shareholders)
        
        # Vérifications de performance
        assert result.stats.mean < 0.2  # Moins de 200ms en moyenne
        assert result.stats.max < 1.0   # Moins de 1s au maximum
    
    def test_create_shareholder_performance(self, performance_client: TestClient, benchmark):
        """Test de performance pour la création d'actionnaire"""
        
        shareholder_data = {
            "username": "perftest",
            "email": "perftest@example.com",
            "first_name": "Performance",
            "last_name": "Test",
            "company_name": "Performance Test Company",
            "phone": "+1234567890"
        }
        
        def create_shareholder():
            response = performance_client.post("/api/shareholders/", json=shareholder_data)
            assert response.status_code in [200, 201]
        
        # Benchmark de l'endpoint
        result = benchmark(create_shareholder)
        
        # Vérifications de performance
        assert result.stats.mean < 0.5  # Moins de 500ms en moyenne
        assert result.stats.max < 2.0   # Moins de 2s au maximum
    
    def test_get_issuances_performance(self, performance_client: TestClient, benchmark):
        """Test de performance pour la récupération des émissions"""
        
        def get_issuances():
            response = performance_client.get("/api/issuances/")
            assert response.status_code == 200
        
        # Benchmark de l'endpoint
        result = benchmark(get_issuances)
        
        # Vérifications de performance
        assert result.stats.mean < 0.3  # Moins de 300ms en moyenne
        assert result.stats.max < 1.5   # Moins de 1.5s au maximum
    
    def test_create_issuance_performance(self, performance_client: TestClient, benchmark):
        """Test de performance pour la création d'émission"""
        
        issuance_data = {
            "shareholder_id": "550e8400-e29b-41d4-a716-446655440000",
            "number_of_shares": 100,
            "price_per_share": 10.50,
            "total_amount": 1050.00,
            "issue_date": "2024-01-01T00:00:00"
        }
        
        def create_issuance():
            response = performance_client.post("/api/issuances/", json=issuance_data)
            assert response.status_code in [200, 201]
        
        # Benchmark de l'endpoint
        result = benchmark(create_issuance)
        
        # Vérifications de performance
        assert result.stats.mean < 1.0  # Moins de 1s en moyenne
        assert result.stats.max < 3.0   # Moins de 3s au maximum
    
    def test_audit_events_performance(self, performance_client: TestClient, benchmark):
        """Test de performance pour la récupération des événements d'audit"""
        
        def get_audit_events():
            response = performance_client.get("/api/audit/events")
            assert response.status_code == 200
        
        # Benchmark de l'endpoint
        result = benchmark(get_audit_events)
        
        # Vérifications de performance
        assert result.stats.mean < 0.4  # Moins de 400ms en moyenne
        assert result.stats.max < 2.0   # Moins de 2s au maximum
    
    def test_concurrent_requests_performance(self, performance_client: TestClient):
        """Test de performance pour les requêtes concurrentes"""
        import threading
        import concurrent.futures
        
        results = []
        errors = []
        
        def make_request():
            try:
                start_time = time.time()
                response = performance_client.get("/health")
                end_time = time.time()
                
                if response.status_code == 200:
                    results.append(end_time - start_time)
                else:
                    errors.append(f"Status code: {response.status_code}")
            except Exception as e:
                errors.append(str(e))
        
        # Exécuter 10 requêtes concurrentes
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            concurrent.futures.wait(futures)
        
        # Vérifications
        assert len(errors) == 0, f"Erreurs lors des requêtes concurrentes: {errors}"
        assert len(results) == 10, "Toutes les requêtes doivent être exécutées"
        
        # Calculer les statistiques
        avg_time = sum(results) / len(results)
        max_time = max(results)
        
        # Vérifications de performance
        assert avg_time < 0.2, f"Temps moyen trop élevé: {avg_time:.3f}s"
        assert max_time < 1.0, f"Temps maximum trop élevé: {max_time:.3f}s"
    
    def test_memory_usage_performance(self, performance_client: TestClient):
        """Test de performance pour l'utilisation mémoire"""
        import psutil
        import os
        
        # Obtenir le processus Python actuel
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Effectuer plusieurs requêtes
        for _ in range(100):
            response = performance_client.get("/health")
            assert response.status_code == 200
        
        # Vérifier l'utilisation mémoire
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # L'augmentation mémoire ne doit pas dépasser 50MB
        assert memory_increase < 50, f"Augmentation mémoire trop élevée: {memory_increase:.2f}MB"
    
    def test_database_query_performance(self, performance_session, benchmark):
        """Test de performance pour les requêtes de base de données"""
        from app.database.models import ShareholderProfile, ShareIssuance
        
        def query_shareholders():
            shareholders = performance_session.query(ShareholderProfile).all()
            return len(shareholders)
        
        def query_issuances():
            issuances = performance_session.query(ShareIssuance).all()
            return len(issuances)
        
        def query_join():
            result = performance_session.query(
                ShareholderProfile, ShareIssuance
            ).join(
                ShareIssuance, ShareholderProfile.id == ShareIssuance.shareholder_id
            ).all()
            return len(result)
        
        # Benchmarks
        shareholders_result = benchmark(query_shareholders)
        issuances_result = benchmark(query_issuances)
        join_result = benchmark(query_join)
        
        # Vérifications de performance
        assert shareholders_result.stats.mean < 0.1, "Requête shareholders trop lente"
        assert issuances_result.stats.mean < 0.1, "Requête issuances trop lente"
        assert join_result.stats.mean < 0.2, "Requête join trop lente"
    
    def test_event_bus_performance(self, benchmark):
        """Test de performance pour le bus d'événements"""
        from app.core.events import event_bus, Event, EventType
        
        def publish_event():
            event = Event(
                type=EventType.AUDIT_LOG,
                payload={"test": "data"},
                metadata={"source": "test"}
            )
            event_bus.publish(event)
        
        # Benchmark de la publication d'événements
        result = benchmark(publish_event)
        
        # Vérifications de performance
        assert result.stats.mean < 0.01, "Publication d'événement trop lente"
        assert result.stats.max < 0.1, "Publication d'événement trop lente (max)"
    
    def test_certificate_generation_performance(self, benchmark):
        """Test de performance pour la génération de certificats"""
        from app.services.certificate_service import CertificateService
        
        def generate_certificate():
            # Mock des données pour la génération
            certificate_data = {
                "shareholder_name": "Test User",
                "shares_count": 100,
                "share_price": 10.50,
                "total_amount": 1050.00,
                "issue_date": "2024-01-01"
            }
            
            # Simuler la génération (mock)
            return CertificateService.generate_certificate(certificate_data)
        
        # Benchmark de la génération
        result = benchmark(generate_certificate)
        
        # Vérifications de performance
        assert result.stats.mean < 2.0, "Génération de certificat trop lente"
        assert result.stats.max < 5.0, "Génération de certificat trop lente (max)"

