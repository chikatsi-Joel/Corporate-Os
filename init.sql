-- Création de la base de données pour Keycloak
CREATE DATABASE keycloak;

-- Connexion à la base de données corporate_os
\c corporate_os;

-- Extension pour UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keycloak_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'actionnaire')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des profils d'actionnaires non utilisé mais idéale
CREATE TABLE IF NOT EXISTS shareholder_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(255),
    address TEXT,
    phone VARCHAR(50),
    tax_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des émissions d'actions
CREATE TABLE IF NOT EXISTS share_issuances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shareholder_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    number_of_shares INTEGER NOT NULL CHECK (number_of_shares > 0),
    price_per_share NUMERIC(10, 2) NOT NULL CHECK (price_per_share >= 0),
    total_amount NUMERIC(12, 2) NOT NULL,
    issue_date TIMESTAMP NOT NULL,
    certificate_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'issued' CHECK (status IN ('pending', 'issued', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('share_issuance', 'share_transfer', 'certificate_generated', 'system_alert', 'user_registration', 'cap_table_update')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'read')),
    read_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    metadata TEXT, -- JSON pour stocker des données supplémentaires
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des événements d'audit
CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('audit', 'system', 'user', 'resource')),
    event_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    user_role VARCHAR(50),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    action VARCHAR(100) NOT NULL CHECK (action IN ('create', 'update', 'delete', 'view', 'login', 'logout', 'export')),
    description TEXT,
    event_data TEXT, -- JSON pour les données de l'événement
    previous_data TEXT, -- JSON pour l'état précédent
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'processed' CHECK (status IN ('processed', 'failed', 'pending'))
);

-- Index pour les performances
CREATE INDEX IF NOT EXISTS idx_users_keycloak_id ON users(keycloak_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

CREATE INDEX IF NOT EXISTS idx_shareholder_profiles_user_id ON shareholder_profiles(user_id);

CREATE INDEX IF NOT EXISTS idx_share_issuances_shareholder_id ON share_issuances(shareholder_id);
CREATE INDEX IF NOT EXISTS idx_share_issuances_issue_date ON share_issuances(issue_date);
CREATE INDEX IF NOT EXISTS idx_share_issuances_status ON share_issuances(status);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_action ON audit_events(action);
CREATE INDEX IF NOT EXISTS idx_audit_events_resource_type ON audit_events(resource_type);
CREATE INDEX IF NOT EXISTS idx_audit_events_created_at ON audit_events(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_events_status ON audit_events(status);

-- Index composites pour les requêtes courantes
CREATE INDEX IF NOT EXISTS idx_audit_events_user_date ON audit_events(event_type, user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_events_resource_date ON audit_events(resource_type, resource_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_events_user_date_simple ON audit_events(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_events_date_type ON audit_events(created_at, event_type);

-- Index pour les notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_status ON notifications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_notifications_type_date ON notifications(type, created_at);

-- Index pour les émissions d'actions
CREATE INDEX IF NOT EXISTS idx_share_issuances_shareholder_status ON share_issuances(shareholder_id, status);
CREATE INDEX IF NOT EXISTS idx_share_issuances_date_status ON share_issuances(issue_date, status);

INSERT INTO users (keycloak_id, username, email, first_name, last_name, role)
VALUES
  (
    'keycloak_admin_id1',
    'admin',
    'admin@corporate-os.com',
    'Admin',
    'User',
    'admin'
  ),
  (
    'keycloak_actionnaire_id1',
    'actionnaire',
    'actionnaire@corporate-os.com',
    'Actionnaire',
    'User',
    'actionnaire'
  )
ON CONFLICT (username) DO NOTHING;

-- Fonction pour mettre à jour le timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour mettre à jour automatiquement updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_shareholder_profiles_updated_at BEFORE UPDATE ON shareholder_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_share_issuances_updated_at BEFORE UPDATE ON share_issuances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 