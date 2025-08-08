#!/bin/bash

# Script pour exécuter tous les tests d'audit et d'événements
# Usage: ./run_audit_tests.sh [options]

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_DIR="tests"
COVERAGE_DIR="htmlcov"
COVERAGE_REPORT="coverage.xml"

# Options par défaut
VERBOSE=false
COVERAGE=false
FAIL_FAST=false
PATTERN=""

# Fonction d'aide
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help           Afficher cette aide"
    echo "  -v, --verbose        Mode verbeux"
    echo "  -c, --coverage       Générer un rapport de couverture"
    echo "  -f, --fail-fast      Arrêter au premier échec"
    echo "  -p, --pattern PAT    Filtrer les tests par pattern"
    echo ""
    echo "Exemples:"
    echo "  $0                    # Exécuter tous les tests"
    echo "  $0 -c                 # Avec couverture"
    echo "  $0 -p audit           # Tests contenant 'audit'"
    echo "  $0 -v -c -f           # Verbose, couverture, fail-fast"
}

# Parsing des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -f|--fail-fast)
            FAIL_FAST=true
            shift
            ;;
        -p|--pattern)
            PATTERN="$2"
            shift 2
            ;;
        *)
            echo "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# Vérification de l'environnement
echo -e "${BLUE}🔍 Vérification de l'environnement...${NC}"

# Vérifier que pytest est installé
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest n'est pas installé${NC}"
    echo "Installez-le avec: pip install pytest pytest-cov pytest-asyncio"
    exit 1
fi

# Vérifier que le répertoire de tests existe
if [ ! -d "$TEST_DIR" ]; then
    echo -e "${RED}❌ Le répertoire de tests '$TEST_DIR' n'existe pas${NC}"
    exit 1
fi

# Vérifier que les modules nécessaires existent
required_modules=(
    "core/event_type.py"
    "events/publisher.py"
    "events/consumer.py"
    "audit/service/audit_service.py"
    "audit/api/audit_api.py"
)

for module in "${required_modules[@]}"; do
    if [ ! -f "$module" ]; then
        echo -e "${RED}❌ Module manquant: $module${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ Environnement OK${NC}"

# Construction de la commande pytest
PYTEST_CMD="pytest"

# Ajouter les options
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=core --cov=events --cov=audit --cov=app"
    PYTEST_CMD="$PYTEST_CMD --cov-report=html:$COVERAGE_DIR"
    PYTEST_CMD="$PYTEST_CMD --cov-report=xml:$COVERAGE_REPORT"
    PYTEST_CMD="$PYTEST_CMD --cov-report=term-missing"
fi

if [ "$FAIL_FAST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -x"
fi

# Ajouter le pattern si spécifié
if [ -n "$PATTERN" ]; then
    PYTEST_CMD="$PYTEST_CMD -k $PATTERN"
fi

# Ajouter le répertoire de tests
PYTEST_CMD="$PYTEST_CMD $TEST_DIR"

# Filtrer les tests d'audit et d'événements
AUDIT_TESTS=(
    "test_events_publisher.py"
    "test_events_consumer.py"
    "test_audit_service.py"
    "test_audit_api.py"
    "test_event_types.py"
)

echo -e "${BLUE}🧪 Tests d'audit et d'événements à exécuter:${NC}"
for test_file in "${AUDIT_TESTS[@]}"; do
    if [ -f "$TEST_DIR/$test_file" ]; then
        echo -e "  ✅ $test_file"
    else
        echo -e "  ⚠️  $test_file (non trouvé)"
    fi
done

echo ""
echo -e "${BLUE}🚀 Démarrage des tests...${NC}"
echo "Commande: $PYTEST_CMD"
echo ""

# Exécution des tests
start_time=$(date +%s)

if $PYTEST_CMD; then
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo ""
    echo -e "${GREEN}✅ Tous les tests ont réussi!${NC}"
    echo -e "${GREEN}⏱️  Durée: ${duration}s${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo -e "${BLUE}📊 Rapport de couverture généré:${NC}"
        echo -e "  📁 HTML: $COVERAGE_DIR/index.html"
        echo -e "  📄 XML: $COVERAGE_REPORT"
        
        # Afficher un résumé de la couverture
        if command -v coverage &> /dev/null; then
            echo ""
            echo -e "${BLUE}📈 Résumé de la couverture:${NC}"
            coverage report --show-missing || true
        fi
    fi
    
    exit 0
else
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo ""
    echo -e "${RED}❌ Certains tests ont échoué${NC}"
    echo -e "${RED}⏱️  Durée: ${duration}s${NC}"
    
    if [ "$COVERAGE" = true ] && [ -d "$COVERAGE_DIR" ]; then
        echo ""
        echo -e "${YELLOW}📊 Rapport de couverture disponible:${NC}"
        echo -e "  📁 HTML: $COVERAGE_DIR/index.html"
    fi
    
    exit 1
fi











