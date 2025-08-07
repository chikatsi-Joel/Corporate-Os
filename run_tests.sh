#!/bin/bash

# Script pour exécuter les tests unitaires

echo "🚀 Démarrage des tests unitaires..."

# Vérifier si nous sommes dans le bon répertoire
if [ ! -f "pytest.ini" ]; then
    echo "❌ Erreur: pytest.ini non trouvé. Assurez-vous d'être dans le répertoire racine du projet."
    exit 1
fi

# Installer les dépendances de test si nécessaire
echo "📦 Vérification des dépendances de test..."
pip install -r app/requirements.txt

# Exécuter les tests avec couverture
echo "🧪 Exécution des tests unitaires..."
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Vérifier le code de sortie
if [ $? -eq 0 ]; then
    echo "✅ Tous les tests ont réussi!"
    echo "📊 Rapport de couverture généré dans htmlcov/index.html"
else
    echo "❌ Certains tests ont échoué."
    exit 1
fi
