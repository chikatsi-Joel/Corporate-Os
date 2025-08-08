# 🏢 Corporate OS - Gestion de Cap Table

## 🎯 Ce qui a été réalisé

Corporate OS est une application de gestion de table de capitalisation (Cap Table) qui permet de :

### 👨‍💼 **Fonctionnalités Administrateur**
- **Gestion des actionnaires** : Création, consultation et suivi des actionnaires
- **Émissions d'actions** : Création d'émissions avec calcul automatique des montants
- **Génération de certificats** : Certificats PDF automatiques pour chaque émission
- **Tableau de bord** : Vue d'ensemble de la répartition des actions
- **Audit complet** : Traçabilité de toutes les opérations

### 👤 **Fonctionnalités Actionnaire**
- **Consultation personnelle** : Vue de ses propres actions et certificats
- **Téléchargement** : Accès aux certificats PDF de ses émissions
- **Historique** : Suivi de toutes ses émissions d'actions

### 🔧 **Fonctionnalités Système**
- **Authentification sécurisée** : Intégration avec Keycloak
- **Système d'événements** : Bus d'événements interne pour la traçabilité
- **Validation métier** : Contraintes sur les nombres d'actions et prix
- **Génération PDF** : Certificats automatiques avec filigrane

## 🏗️ Pourquoi cette architecture ?

### 🔐 **Authentification avec Keycloak**
Nous avons choisi Keycloak pour sa **robustesse** et sa **flexibilité** :
- **Standards ouverts** : OAuth2, OpenID Connect, JWT
- **Gestion des rôles** : Admin et Actionnaire avec permissions distinctes
- **Interface d'administration** : Gestion facile des utilisateurs
- **Sécurité** : Authentification centralisée et sécurisée

**Comment nous l'utilisons :**
```python
# Configuration Keycloak dans l'application
config = KeycloakConfiguration(
    url=settings.keycloak_url,
    realm=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
    client_secret=settings.keycloak_client_secret
)
setup_keycloak_middleware(app, config, user_mapper=map_user)
```

### 🚀 **Système d'Événements Interne**
Nous avons développé un **bus d'événements léger** pour :
- **Découpler les modules** : Chaque fonctionnalité peut écouter les événements qui l'intéressent
- **Traçabilité complète** : Toutes les opérations sont enregistrées
- **Extensibilité** : Facile d'ajouter de nouvelles fonctionnalités

**Comment ça fonctionne :**
```python
# Publication d'événement lors d'une émission
@publish_event_async(EventType.SHARE_ISSUED, source="issuance_service")
def create_issuance(db: Session, issuance_data: ShareIssuanceCreate):
    # Logique métier
    return new_issuance

# Écoute d'événement pour l'audit
@event_handler(EventType.AUDIT_LOG)
def handle_audit_persistence(event: Event):
    # Persistance en base de données
    pass
```

### 🎯 **Avantages de cette approche**
- **Monolithique évolutif** : Architecture simple mais extensible
- **Traçabilité** : Chaque action est enregistrée automatiquement
- **Sécurité** : Authentification robuste avec Keycloak
- **Maintenabilité** : Code découplé et modulaire

## 🚀 **Démarrage Rapide**

### 📋 **Prérequis**
- Docker et Docker Compose installés
- Git
- 4GB RAM minimum
- 2GB espace disque libre
- Ports 8000, 8080, 5432 disponibles

### ⚡ **Démarrage en 3 étapes**

#### **1. Cloner et configurer**
```bash
# Cloner le projet
git clone https://github.com/chikatsi-Joel/Corporate-Os.git
cd Corporate-Os


```

#### **2. Démarrer les services**
```bash
# Démarrer tous les services
docker compose up -d --build

# Vérifier que tout fonctionne
docker compose ps
```

#### **3. Accéder à l'application**
- **Application** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs
- **Keycloak** : http://localhost:8080 (admin/admin)

### 👥 **Utilisateurs par défaut**
- **Admin** : `admin` / `admin123`
- **Actionnaire** : `actionnaire` / `actionnaire123`

## 🔍 **Vérification du démarrage**

### **1. Vérifier les services**
```bash
# Statut des conteneurs
docker compose ps

# Logs en temps réel
docker compose logs -f
```

### **2. Vérifier l'API**
```bash
# Test de santé
curl http://localhost:8000/health

# Test de l'endpoint principal
curl http://localhost:8000/
```

### **3. Vérifier Keycloak**
```bash
# Test de connexion Keycloak
curl http://localhost:8080/health
```

## 🛠️ **Commandes utiles**

### **Gestion des services**
```bash
# Redémarrer un service
docker compose restart app

# Voir les logs d'un service
docker compose logs -f postgres

# Arrêter tous les services
docker compose down

# Nettoyer complètement (volumes inclus)
docker compose down -v
```

### **Base de données**
```bash
# Accéder à PostgreSQL
docker compose exec postgres psql -U corporate_user -d corporate_os

# Appliquer les migrations
docker compose exec app alembic upgrade head

# Voir les tables
docker compose exec postgres psql -U corporate_user -d corporate_os -c "\dt"
```

### **Tests**
```bash
# Lancer les tests
docker compose exec app pytest

# Tests avec couverture
docker compose exec app pytest --cov=app
```

## 🔧 **Dépannage**

### **Problème de ports**
```bash
# Vérifier les ports utilisés
netstat -tulpn | grep -E ':(8000|8080|5432)'

# Arrêter les services qui utilisent ces ports
sudo lsof -ti:8000 | xargs kill -9
```

### **Problème de démarrage**
```bash
# Nettoyer et redémarrer
docker compose down -v
docker compose up -d

# Vérifier les logs
docker compose logs -f
```

### **Problème de permissions**
```bash
# Corriger les permissions
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
```

## 📊 **Structure du projet**

```
Corporate-Os/
├── app/                          # Application principale
│   ├── api/                     # Endpoints API
│   ├── core/                    # Configuration et utilitaires
│   ├── database/                # Modèles et migrations
│   ├── services/                # Logique métier
│   └── schemas/                 # Validation des données
├── bus_event/                   # Système d'événements
│   └── events/                  # Bus d'événements et handlers
├── keycloak/                    # Configuration Keycloak
├── certificates/                # Certificats générés
├── uploads/                     # Fichiers uploadés
├── docker-compose.yml          # Orchestration des services
├── Dockerfile                  # Image de l'application
└── README.md                   # Ce fichier
```

## 🎯 **Points clés du code**

### **1. Modèles de données**
```python
# app/database/models.py
class ShareIssuance(Base):
    __table_args__ = (
        CheckConstraint(number_of_shares > 0, name='positive_shares'),
        CheckConstraint(price_per_share >= 0, name='non_negative_price'),
    )
```

### **2. Système d'événements**
```python
# bus_event/events/event_bus.py
class EventBus:
    def publish(self, event: Event) -> bool:
        self._handle_sync(event)
        asyncio.create_task(self._event_queue.put(event))
```

### **3. Authentification**
```python
# app/core/check_role.py
def require_role(role: str):
    def role_checker(request: Request):
        user_info = request.state.user
        if role not in user_info['realm_access']['roles']:
            raise HTTPException(status_code=403, detail="Accès refusé")
    return role_checker
```

## 🚀 **Évolution future**

- **Interface web** : Frontend React/Vue.js
- **Notifications** : Emails automatiques
- **Reporting** : Rapports et analytics
- **API publique** : Documentation complète
- **Tests automatisés** : Couverture complète

---

## 📞 **Support**

Pour toute question ou problème :
1. Vérifiez la section **Dépannage** ci-dessus
2. Consultez les logs : `docker compose logs -f`
3. Testez l'API : http://localhost:8000/docs

**Corporate OS** - Gestion simplifiée de votre table de capitalisation 🏢