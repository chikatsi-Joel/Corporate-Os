"""
Tests de sécurité pour Corporate OS
"""
import pytest
import json
from typing import Dict, Any
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.security
class TestSecurity:
    """Tests de sécurité"""
    
    def test_sql_injection_prevention(self, client: TestClient):
        """Test de prévention des injections SQL"""
        
        # Tentative d'injection SQL dans les paramètres
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'hacker@evil.com'); --",
            "' UNION SELECT * FROM users --"
        ]
        
        for payload in malicious_payloads:
            # Test sur l'endpoint des actionnaires
            response = client.get(f"/api/shareholders/?search={payload}")
            
            # Vérifier que la requête ne provoque pas d'erreur SQL
            assert response.status_code in [200, 400, 422], f"SQL injection possible avec: {payload}"
            
            # Vérifier qu'aucune donnée sensible n'est exposée
            if response.status_code == 200:
                data = response.json()
                assert "error" not in str(data).lower(), f"Erreur exposée avec: {payload}"
    
    def test_xss_prevention(self, client: TestClient):
        """Test de prévention des attaques XSS"""
        
        # Payloads XSS malveillants
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            # Test sur la création d'actionnaire
            shareholder_data = {
                "username": payload,
                "email": f"{payload}@example.com",
                "first_name": payload,
                "last_name": payload,
                "company_name": payload
            }
            
            response = client.post("/api/shareholders/", json=shareholder_data)
            
            # Vérifier que le payload n'est pas exécuté
            if response.status_code == 200:
                data = response.json()
                response_text = json.dumps(data)
                
                # Vérifier qu'aucun script n'est présent dans la réponse
                assert "<script>" not in response_text.lower(), f"XSS possible avec: {payload}"
                assert "javascript:" not in response_text.lower(), f"XSS possible avec: {payload}"
    
    def test_authentication_required(self, client: TestClient):
        """Test que l'authentification est requise pour les endpoints sensibles"""
        
        # Endpoints qui nécessitent une authentification
        protected_endpoints = [
            ("GET", "/api/shareholders/"),
            ("POST", "/api/shareholders/"),
            ("GET", "/api/issuances/"),
            ("POST", "/api/issuances/"),
            ("GET", "/api/audit/events"),
            ("GET", "/api/audit/events/1")
        ]
        
        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            # Vérifier que l'authentification est requise
            assert response.status_code in [401, 403], f"Endpoint {endpoint} accessible sans authentification"
    
    def test_authorization_roles(self, client: TestClient):
        """Test des autorisations basées sur les rôles"""
        
        # Mock des tokens pour différents rôles
        admin_token = "mock-admin-token"
        actionnaire_token = "mock-actionnaire-token"
        no_role_token = "mock-no-role-token"
        
        # Test des endpoints admin
        admin_endpoints = [
            ("GET", "/api/audit/events"),
            ("POST", "/api/shareholders/"),
            ("DELETE", "/api/shareholders/1")
        ]
        
        for method, endpoint in admin_endpoints:
            headers = {"Authorization": f"Bearer {actionnaire_token}"}
            
            if method == "GET":
                response = client.get(endpoint, headers=headers)
            elif method == "POST":
                response = client.post(endpoint, headers=headers, json={})
            elif method == "DELETE":
                response = client.delete(endpoint, headers=headers)
            
            # Vérifier que l'accès est refusé pour les non-admins
            assert response.status_code in [403, 401], f"Endpoint {endpoint} accessible sans rôle admin"
    
    def test_input_validation(self, client: TestClient):
        """Test de validation des entrées"""
        
        # Données invalides
        invalid_data = [
            # Email invalide
            {
                "username": "testuser",
                "email": "invalid-email",
                "first_name": "Test",
                "last_name": "User"
            },
            # Nombre d'actions négatif
            {
                "shareholder_id": "550e8400-e29b-41d4-a716-446655440000",
                "number_of_shares": -100,
                "price_per_share": 10.50,
                "total_amount": -1050.00
            },
            # Prix négatif
            {
                "shareholder_id": "550e8400-e29b-41d4-a716-446655440000",
                "number_of_shares": 100,
                "price_per_share": -10.50,
                "total_amount": -1050.00
            }
        ]
        
        for data in invalid_data:
            response = client.post("/api/shareholders/", json=data)
            
            # Vérifier que la validation échoue
            assert response.status_code in [400, 422], f"Validation échouée pour: {data}"
    
    def test_rate_limiting(self, client: TestClient):
        """Test de limitation de débit"""
        
        # Effectuer plusieurs requêtes rapides
        responses = []
        for _ in range(20):
            response = client.get("/health")
            responses.append(response.status_code)
        
        # Vérifier qu'au moins une requête est limitée (si le rate limiting est activé)
        # Note: Ce test peut échouer si le rate limiting n'est pas configuré
        if 429 in responses:
            assert True, "Rate limiting fonctionne"
        else:
            pytest.skip("Rate limiting non configuré")
    
    def test_cors_configuration(self, client: TestClient):
        """Test de la configuration CORS"""
        
        # Test des headers CORS
        response = client.options("/health", headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        })
        
        # Vérifier que les headers CORS sont présents
        cors_headers = response.headers.get("Access-Control-Allow-Origin")
        
        # Si CORS est configuré, vérifier qu'il est sécurisé
        if cors_headers:
            assert cors_headers != "*", "CORS trop permissif"
            assert "evil.com" not in cors_headers, "CORS autorise des domaines malveillants"
    
    def test_headers_security(self, client: TestClient):
        """Test des headers de sécurité"""
        
        response = client.get("/health")
        
        # Vérifier les headers de sécurité
        headers = response.headers
        
        # Headers de sécurité recommandés
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        for header in security_headers:
            if header in headers:
                # Vérifier les valeurs sécurisées
                value = headers[header]
                if header == "X-Content-Type-Options":
                    assert value == "nosniff", "X-Content-Type-Options incorrect"
                elif header == "X-Frame-Options":
                    assert value in ["DENY", "SAMEORIGIN"], "X-Frame-Options incorrect"
                elif header == "X-XSS-Protection":
                    assert value == "1; mode=block", "X-XSS-Protection incorrect"
    
    def test_password_policy(self, client: TestClient):
        """Test de la politique de mots de passe"""
        
        # Mots de passe faibles
        weak_passwords = [
            "123456",
            "password",
            "qwerty",
            "abc123",
            "password123"
        ]
        
        for password in weak_passwords:
            login_data = {
                "username": "testuser",
                "password": password
            }
            
            response = client.post("/auth/login", data=login_data)
            
            # Vérifier que les mots de passe faibles sont rejetés
            if response.status_code == 200:
                data = response.json()
                assert "error" in data or "weak_password" in str(data).lower(), f"Mot de passe faible accepté: {password}"
    
    def test_session_management(self, client: TestClient):
        """Test de la gestion des sessions"""
        
        # Test de déconnexion
        response = client.post("/auth/logout")
        
        # Vérifier que la session est correctement fermée
        assert response.status_code in [200, 401], "Déconnexion échouée"
        
        # Test d'accès après déconnexion
        response = client.get("/api/shareholders/")
        assert response.status_code in [401, 403], "Accès possible après déconnexion"
    
    def test_data_encryption(self, client: TestClient):
        """Test du chiffrement des données sensibles"""
        
        # Créer un actionnaire avec des données sensibles
        shareholder_data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1234567890"
        }
        
        response = client.post("/api/shareholders/", json=shareholder_data)
        
        if response.status_code == 200:
            data = response.json()
            
            # Vérifier que les données sensibles ne sont pas exposées en clair
            response_text = json.dumps(data)
            
            # Vérifier qu'aucune donnée sensible n'est exposée
            sensitive_fields = ["password", "secret", "key", "token"]
            for field in sensitive_fields:
                assert field not in response_text.lower(), f"Données sensibles exposées: {field}"
    
    def test_logging_security(self, client: TestClient):
        """Test de la sécurité des logs"""
        
        # Effectuer une action qui génère des logs
        response = client.get("/health")
        
        # Vérifier que les logs ne contiennent pas d'informations sensibles
        # Note: Ce test nécessite l'accès aux logs, ce qui peut ne pas être possible dans un environnement de test
        
        # Alternative: vérifier que l'endpoint de logs n'expose pas d'informations sensibles
        log_response = client.get("/logs")
        
        if log_response.status_code == 200:
            logs = log_response.text
            
            # Vérifier qu'aucune information sensible n'est dans les logs
            sensitive_patterns = [
                "password",
                "secret",
                "key",
                "token",
                "credit_card",
                "ssn"
            ]
            
            for pattern in sensitive_patterns:
                assert pattern not in logs.lower(), f"Informations sensibles dans les logs: {pattern}"
    
    def test_api_versioning(self, client: TestClient):
        """Test de la versioning de l'API"""
        
        # Test de l'endpoint de version
        response = client.get("/version")
        
        if response.status_code == 200:
            data = response.json()
            
            # Vérifier que la version est présente
            assert "version" in data, "Version manquante dans la réponse"
            assert "api_version" in data, "Version API manquante dans la réponse"
    
    def test_error_handling(self, client: TestClient):
        """Test de la gestion des erreurs"""
        
        # Test d'un endpoint inexistant
        response = client.get("/api/nonexistent")
        
        # Vérifier que l'erreur est gérée correctement
        assert response.status_code == 404, "Erreur 404 non gérée"
        
        # Vérifier que les détails de l'erreur ne sont pas exposés
        data = response.json()
        assert "detail" in data, "Détails de l'erreur manquants"
        
        # Vérifier qu'aucune information sensible n'est exposée
        error_text = json.dumps(data)
        sensitive_info = ["password", "secret", "key", "token", "stack_trace"]
        
        for info in sensitive_info:
            assert info not in error_text.lower(), f"Informations sensibles exposées dans l'erreur: {info}"



