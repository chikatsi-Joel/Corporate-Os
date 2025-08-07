#!/bin/bash

# Script d'initialisation pour importer le realm Keycloak

echo "Attente du démarrage de Keycloak..."
sleep 30

# Attendre que Keycloak soit prêt
echo "Vérification de la disponibilité de Keycloak..."
for i in {1..30}; do
    if curl -f http://localhost:8080/health/ready > /dev/null 2>&1; then
        echo "Keycloak est prêt!"
        break
    fi
    echo "Tentative $i/30 - Keycloak n'est pas encore prêt, attente..."
    sleep 10
done

# Vérifier si Keycloak est prêt
if ! curl -f http://localhost:8080/health/ready > /dev/null 2>&1; then
    echo "Erreur: Keycloak n'est pas prêt après 5 minutes d'attente"
    exit 1
fi

echo "Keycloak est prêt, import du realm..."

# Vérifier si le fichier de realm existe
if [ ! -f "/opt/keycloak/data/import/corporate-os-realm.json" ]; then
    echo "Erreur: Le fichier de realm n'existe pas"
    exit 1
fi

# Importer le realm
echo "Import du realm corporate-os..."
/opt/keycloak/bin/kc.sh import \
    --db=postgres \
    --db-url=jdbc:postgresql://postgres:5432/keycloak \
    --db-username=corporate_user \
    --db-password=corporate_password \
    --file=/opt/keycloak/data/import/corporate-os-realm.json \
    --override=true

if [ $? -eq 0 ]; then
    echo "Realm importé avec succès!"
else
    echo "Erreur lors de l'import du realm"
    exit 1
fi
