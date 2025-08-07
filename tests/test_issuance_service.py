import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.database import Base
from app.database.models import User, ShareIssuance
from app.services.issuance_service import IssuanceService
from app.schemas.issuance import ShareIssuanceCreate


class TestIssuanceService:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Configuration de la base de données de test"""
        # Base de données en mémoire pour les tests
        self.engine = create_engine("sqlite:///:memory:")
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        
        # Créer un utilisateur de test
        self.db = self.TestingSessionLocal()
        self.test_user = User(
            id=uuid4(),
            keycloak_id="test-keycloak-id",
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role="actionnaire"
        )
        self.db.add(self.test_user)
        self.db.commit()
        
        yield
        
        self.db.close()
    
    def test_create_issuance(self):
        """Test de création d'une émission d'actions"""
        issuance_data = ShareIssuanceCreate(
            shareholder_id=self.test_user.id,
            number_of_shares=100,
            price_per_share=Decimal("10.50"),
            issue_date=date.today()
        )
        
        issuance = IssuanceService.create_issuance(self.db, issuance_data)
        
        assert issuance.shareholder_id == self.test_user.id
        assert issuance.number_of_shares == 100
        assert issuance.price_per_share == Decimal("10.50")
        assert issuance.total_amount == Decimal("1050.00")
        assert issuance.status == "issued"
    
    def test_get_shareholder_summary(self):
        """Test de récupération du résumé d'un actionnaire"""
        # Créer plusieurs émissions
        issuance1 = ShareIssuance(
            shareholder_id=self.test_user.id,
            number_of_shares=100,
            price_per_share=Decimal("10.00"),
            total_amount=Decimal("1000.00"),
            issue_date=date.today(),
            status="issued"
        )
        
        issuance2 = ShareIssuance(
            shareholder_id=self.test_user.id,
            number_of_shares=50,
            price_per_share=Decimal("20.00"),
            total_amount=Decimal("1000.00"),
            issue_date=date.today(),
            status="issued"
        )
        
        self.db.add(issuance1)
        self.db.add(issuance2)
        self.db.commit()
        
        summary = IssuanceService.get_shareholder_summary(self.db, self.test_user.id)
        
        assert summary["total_shares"] == 150
        assert summary["total_value"] == 2000.0
        assert summary["total_issuances"] == 2
    
    def test_get_cap_table_summary(self):
        """Test de récupération du résumé de la table de capitalisation"""
        # Créer un deuxième utilisateur
        user2 = User(
            id=uuid4(),
            keycloak_id="test-keycloak-id-2",
            username="testuser2",
            email="test2@example.com",
            first_name="Test2",
            last_name="User2",
            role="actionnaire"
        )
        self.db.add(user2)
        self.db.commit()
        
        # Créer des émissions pour les deux utilisateurs
        issuance1 = ShareIssuance(
            shareholder_id=self.test_user.id,
            number_of_shares=100,
            price_per_share=Decimal("10.00"),
            total_amount=Decimal("1000.00"),
            issue_date=date.today(),
            status="issued"
        )
        
        issuance2 = ShareIssuance(
            shareholder_id=user2.id,
            number_of_shares=50,
            price_per_share=Decimal("20.00"),
            total_amount=Decimal("1000.00"),
            issue_date=date.today(),
            status="issued"
        )
        
        self.db.add(issuance1)
        self.db.add(issuance2)
        self.db.commit()
        
        summary = IssuanceService.get_cap_table_summary(self.db)
        
        assert summary["total_shares"] == 150
        assert summary["total_value"] == 2000.0
        assert len(summary["shareholders"]) == 2
        
        # Vérifier les pourcentages
        user1_data = next(s for s in summary["shareholders"] if s["username"] == "testuser")
        user2_data = next(s for s in summary["shareholders"] if s["username"] == "testuser2")
        
        assert user1_data["percentage"] == 66.67  # 100/150 * 100
        assert user2_data["percentage"] == 33.33  # 50/150 * 100 