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
    user_type VARCHAR(50) NOT NULL CHECK (user_type IN ('admin', 'actionnaire')),
    last_name VARCHAR(255),
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


-- Table des événements d'audit
CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL ,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    user_email VARCHAR(255),
    user_role VARCHAR(50),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    description TEXT,
    event_data TEXT, -- JSON pour les données de l'événement
    previous_data TEXT, -- JSON pour l'état précédent
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'processed' CHECK (status IN ('processed', 'failed', 'pending'))
);



INSERT INTO users (keycloak_id, username, email, first_name, last_name, user_type)
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

CREATE TRIGGER update_share_issuances_updated_at BEFORE UPDATE ON share_issuances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 