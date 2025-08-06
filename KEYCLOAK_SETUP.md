# 🔐 Intégration Keycloak - Guide d'Installation

Ce guide vous accompagne dans l'intégration de Keycloak pour la gestion de l'authentification et de l'autorisation de votre application de gestion des actions.

## 🎯 Avantages de Keycloak

- ✅ **Authentification centralisée** : Gestion unifiée des utilisateurs
- ✅ **SSO (Single Sign-On)** : Connexion unique pour plusieurs applications
- ✅ **Gestion des rôles** : Contrôle d'accès granulaire
- ✅ **Interface d'administration** : Interface web intuitive
- ✅ **Standards ouverts** : OAuth2, OpenID Connect, SAML
- ✅ **Haute sécurité** : Chiffrement, audit, conformité

## 🚀 Installation Rapide

### Option 1 : Script Automatique (Recommandé)

```bash
# Installer les dépendances Python pour le script
pip install requests

# Lancer le script de démarrage complet
python scripts/start_with_keycloak.py
```

Ce script va :
1. Démarrer tous les services Docker
2. Attendre que Keycloak soit prêt
3. Configurer automatiquement Keycloak
4. Créer les utilisateurs par défaut

### Option 2 : Démarrage Manuel

```bash
# 1. Démarrer tous les services
docker-compose up -d

# 2. Attendre que les services soient prêts (2-3 minutes)
# Vérifier que Keycloak est accessible
curl http://localhost:8080/health

# 3. Configurer Keycloak automatiquement
python scripts/setup_keycloak.py
```

## 📋 Configuration Manuelle (Alternative)

Si vous préférez configurer Keycloak manuellement :

### 1. Accéder à l'Interface d'Administration

- **URL** : http://localhost:8080
- **Utilisateur** : `admin`
- **Mot de passe** : `admin`

### 2. Créer un Realm

1. Cliquer sur "Create Realm"
2. Nom : `actions-realm`
3. Description : "Actions Management Realm"

### 3. Créer un Client

1. Aller dans "Clients" → "Create"
2. Client ID : `actions-api`
3. Client Protocol : `openid-connect`
4. Root URL : `http://localhost:8000`

### 4. Créer les Rôles

1. Aller dans "Roles" → "Add Role"
2. Créer les rôles :
   - `admin`
   - `shareholder`

### 5. Créer les Utilisateurs

1. Aller dans "Users" → "Add User"
2. Créer les utilisateurs :

**Admin :**
- Username : `admin`
- Email : `admin@example.com`
- First Name : `Admin`
- Last Name : `User`
- Credentials : `admin123`
- Roles : `admin`

**Actionnaire :**
- Username : `shareholder`
- Email : `shareholder@example.com`
- First Name : `Shareholder`
- Last Name : `User`
- Credentials : `shareholder123`
- Roles : `shareholder`

## 🔧 Configuration de l'Application

### Variables d'Environnement

```env
# Configuration Keycloak
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=actions-realm
KEYCLOAK_CLIENT_ID=actions-api
KEYCLOAK_CLIENT_SECRET=your-client-secret-here
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=admin
KEYCLOAK_TOKEN_EXPIRE_MINUTES=30
```

### Obtenir le Client Secret

1. Aller dans Keycloak Admin → Clients → `actions-api`
2. Onglet "Credentials"
3. Copier le "Client Secret"

## 🧪 Test de l'Intégration

### 1. Tester la Connexion

```bash
# Tester l'endpoint de santé Keycloak
curl http://localhost:8000/api/v1/keycloak/health
```

### 2. Tester l'Authentification

```bash
# Connexion avec l'admin
curl -X POST "http://localhost:8000/api/v1/keycloak/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
```

### 3. Tester les Endpoints Protégés

```bash
# Utiliser le token obtenu
TOKEN="your-access-token-here"

# Tester l'endpoint protégé
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/keycloak/me
```

## 🐳 Configuration Docker

### Services Inclus

Le fichier `docker-compose.yml` inclut maintenant :

1. **actions-db** : Base de données PostgreSQL pour l'application
2. **keycloak-db** : Base de données PostgreSQL pour Keycloak
3. **keycloak** : Serveur Keycloak pour l'authentification
4. **actions-app** : Application FastAPI

### Commandes Utiles

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Voir les logs d'un service spécifique
docker-compose logs -f keycloak

# Arrêter les services
docker-compose down

# Redémarrer un service
docker-compose restart keycloak

# Reconstruire l'application
docker-compose build app
```

### Ports Utilisés

- **8000** : Application FastAPI
- **8080** : Interface Keycloak
- **5432** : Base de données application (externe)
- **5433** : Base de données Keycloak (interne)

## 🔄 Migration depuis l'Authentification Locale

### 1. Sauvegarder les Données

```bash
# Exporter les utilisateurs existants
python scripts/export_users.py
```

### 2. Importer dans Keycloak

```bash
# Importer les utilisateurs dans Keycloak
python scripts/import_users_to_keycloak.py
```

### 3. Mettre à Jour l'Application

```bash
# Basculer vers Keycloak
export USE_KEYCLOAK=true
python run.py
```

## 🛠️ Endpoints Keycloak

### Authentification

- `POST /api/v1/keycloak/login` - Connexion
- `POST /api/v1/keycloak/refresh` - Rafraîchir le token
- `GET /api/v1/keycloak/me` - Informations utilisateur
- `POST /api/v1/keycloak/logout` - Déconnexion

### Gestion des Utilisateurs (Admin)

- `POST /api/v1/keycloak/users` - Créer un utilisateur
- `GET /api/v1/keycloak/users` - Liste des utilisateurs
- `GET /api/v1/keycloak/users/{username}` - Détails utilisateur
- `PUT /api/v1/keycloak/users/{user_id}` - Modifier un utilisateur
- `DELETE /api/v1/keycloak/users/{user_id}` - Supprimer un utilisateur

### Utilitaires

- `GET /api/v1/keycloak/roles` - Rôles de l'utilisateur
- `GET /api/v1/keycloak/health` - Santé de la connexion

## 🔒 Sécurité

### Bonnes Pratiques

1. **Changer les mots de passe par défaut**
2. **Utiliser HTTPS en production**
3. **Configurer les politiques de mots de passe**
4. **Activer l'authentification à deux facteurs**
5. **Configurer les sessions et timeouts**

### Configuration de Production

```env
# Production
KEYCLOAK_SERVER_URL=https://keycloak.yourdomain.com
KEYCLOAK_CLIENT_SECRET=very-secure-client-secret
KEYCLOAK_ADMIN_PASSWORD=very-secure-admin-password
```

## 🐛 Dépannage

### Problèmes Courants

1. **Keycloak non accessible**
   ```bash
   # Vérifier que le conteneur est démarré
   docker ps | grep keycloak
   
   # Vérifier les logs
   docker logs keycloak
   ```

2. **Erreur d'authentification**
   ```bash
   # Vérifier la configuration
   curl http://localhost:8000/api/v1/keycloak/health
   ```

3. **Token invalide**
   ```bash
   # Vérifier l'expiration du token
   # Rafraîchir le token si nécessaire
   ```

### Logs et Debug

```bash
# Activer les logs détaillés
export LOG_LEVEL=DEBUG
python run.py

# Voir les logs Docker
docker-compose logs -f
```

## 📚 Ressources

- [Documentation Keycloak](https://www.keycloak.org/documentation)
- [Guide OpenID Connect](https://openid.net/connect/)
- [OAuth 2.0 Specification](https://oauth.net/2/)

## 🤝 Support

Pour toute question ou problème :
1. Vérifier les logs Keycloak
2. Consulter la documentation officielle
3. Vérifier la configuration réseau
4. Contacter l'équipe de développement 