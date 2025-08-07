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

-- Table des profils d'actionnaires
CREATE TABLE IF NOT EXISTS shareholder_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
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
    shareholder_id UUID REFERENCES users(id) ON DELETE CASCADE,
    number_of_shares INTEGER NOT NULL CHECK (number_of_shares > 0),
    price_per_share DECIMAL(10,2) NOT NULL CHECK (price_per_share >= 0),
    total_amount DECIMAL(12,2) NOT NULL,
    issue_date DATE NOT NULL,
    certificate_path VARCHAR(500),
    status VARCHAR(50) DEFAULT 'issued' CHECK (status IN ('pending', 'issued', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les performances
-- Index sur les colonnes fréquemment utilisées pour les recherches
CREATE INDEX IF NOT EXISTS idx_users_keycloak_id ON users(keycloak_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Index sur les relations
CREATE INDEX IF NOT EXISTS idx_shareholder_profiles_user_id ON shareholder_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_share_issuances_shareholder_id ON share_issuances(shareholder_id);
CREATE INDEX IF NOT EXISTS idx_share_issuances_issue_date ON share_issuances(issue_date);
CREATE INDEX IF NOT EXISTS idx_share_issuances_status ON share_issuances(status);

-- Index composites pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_share_issuances_shareholder_date ON share_issuances(shareholder_id, issue_date);
CREATE INDEX IF NOT EXISTS idx_users_role_created ON users(role, created_at);

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