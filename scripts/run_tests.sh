#!/bin/bash

# Script pour exécuter les tests unitaires de Corporate OS
# Usage: ./scripts/run_tests.sh [options]

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration par défaut
TEST_DIR="tests"
COVERAGE_DIR="htmlcov"
COVERAGE_REPORT="coverage.xml"
REPORTS_DIR="test_reports"
PYTEST_CMD="pytest"
VERBOSE=false
COVERAGE=true
PARALLEL=false
PATTERN=""
MARKERS=""

# Fonction d'aide
show_help() {
    echo -e "${BLUE}Script de tests pour Corporate OS${NC}"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Afficher cette aide"
    echo "  -v, --verbose           Mode verbeux"
    echo "  -c, --no-coverage       Désactiver la couverture de code"
    echo "  -p, --parallel          Exécuter les tests en parallèle"
    echo "  -k PATTERN              Filtrer les tests par pattern"
    echo "  -m MARKERS              Filtrer les tests par marqueurs"
    echo "  -d, --directory DIR     Répertoire de tests (défaut: tests)"
    echo "  -r, --reports DIR       Répertoire des rapports (défaut: test_reports)"
    echo "  --unit                  Tests unitaires uniquement"
    echo "  --integration           Tests d'intégration uniquement"
    echo "  --security              Tests de sécurité uniquement"
    echo "  --performance           Tests de performance uniquement"
    echo ""
    echo "Exemples:"
    echo "  $0                      # Tous les tests avec couverture"
    echo "  $0 --unit               # Tests unitaires uniquement"
    echo "  $0 -k test_auth         # Tests contenant 'test_auth'"
    echo "  $0 -m api               # Tests marqués 'api'"
    echo "  $0 --parallel           # Tests en parallèle"
    echo ""
}

# Fonction pour afficher les messages
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Fonction pour vérifier les prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 n'est pas installé"
        exit 1
    fi
    
    # Vérifier pip
    if ! command -v pip &> /dev/null; then
        log_error "pip n'est pas installé"
        exit 1
    fi
    
    # Vérifier pytest
    if ! python3 -c "import pytest" &> /dev/null; then
        log_warning "pytest n'est pas installé, installation..."
        pip install pytest pytest-cov pytest-asyncio pytest-mock
    fi
    
    # Vérifier les dépendances
    if [ ! -f "requirements.txt" ]; then
        log_warning "requirements.txt non trouvé"
    else
        log_info "Installation des dépendances..."
        pip install -r requirements.txt
    fi
    
    log_success "Prérequis vérifiés"
}

# Fonction pour nettoyer les anciens rapports
cleanup_reports() {
    log_info "Nettoyage des anciens rapports..."
    
    if [ -d "$COVERAGE_DIR" ]; then
        rm -rf "$COVERAGE_DIR"
    fi
    
    if [ -f "$COVERAGE_REPORT" ]; then
        rm -f "$COVERAGE_REPORT"
    fi
    
    if [ -d "$REPORTS_DIR" ]; then
        rm -rf "$REPORTS_DIR"
    fi
    
    mkdir -p "$REPORTS_DIR"
    log_success "Nettoyage terminé"
}

# Fonction pour exécuter les tests
run_tests() {
    log_info "Exécution des tests..."
    
    # Construction de la commande pytest
    if [ "$VERBOSE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD -v"
    fi
    
    if [ "$COVERAGE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov=app --cov=core"
        PYTEST_CMD="$PYTEST_CMD --cov-report=html:$COVERAGE_DIR"
        PYTEST_CMD="$PYTEST_CMD --cov-report=xml:$COVERAGE_REPORT"
        PYTEST_CMD="$PYTEST_CMD --cov-report=term-missing"
        PYTEST_CMD="$PYTEST_CMD --cov-fail-under=80"
    fi
    
    if [ "$PARALLEL" = true ]; then
        PYTEST_CMD="$PYTEST_CMD -n auto"
    fi
    
    if [ -n "$PATTERN" ]; then
        PYTEST_CMD="$PYTEST_CMD -k $PATTERN"
    fi
    
    if [ -n "$MARKERS" ]; then
        PYTEST_CMD="$PYTEST_CMD -m $MARKERS"
    fi
    
    # Ajouter le répertoire de tests
    PYTEST_CMD="$PYTEST_CMD $TEST_DIR"
    
    # Exécuter les tests
    log_info "Commande: $PYTEST_CMD"
    echo ""
    
    if $PYTEST_CMD; then
        log_success "Tests terminés avec succès"
        return 0
    else
        log_error "Tests échoués"
        return 1
    fi
}

# Fonction pour générer les rapports
generate_reports() {
    log_info "Génération des rapports..."
    
    # Rapport de couverture HTML
    if [ -d "$COVERAGE_DIR" ]; then
        log_success "Rapport de couverture HTML généré: $COVERAGE_DIR/index.html"
    fi
    
    # Rapport de couverture XML
    if [ -f "$COVERAGE_REPORT" ]; then
        log_success "Rapport de couverture XML généré: $COVERAGE_REPORT"
    fi
    
    # Rapport de tests
    if [ -d "$REPORTS_DIR" ]; then
        echo "Résumé des tests" > "$REPORTS_DIR/test_summary.txt"
        echo "================" >> "$REPORTS_DIR/test_summary.txt"
        echo "Date: $(date)" >> "$REPORTS_DIR/test_summary.txt"
        echo "Tests exécutés: $TEST_DIR" >> "$REPORTS_DIR/test_summary.txt"
        echo "Couverture: $COVERAGE" >> "$REPORTS_DIR/test_summary.txt"
        echo "Parallèle: $PARALLEL" >> "$REPORTS_DIR/test_summary.txt"
        if [ -n "$PATTERN" ]; then
            echo "Pattern: $PATTERN" >> "$REPORTS_DIR/test_summary.txt"
        fi
        if [ -n "$MARKERS" ]; then
            echo "Marqueurs: $MARKERS" >> "$REPORTS_DIR/test_summary.txt"
        fi
        log_success "Rapport de tests généré: $REPORTS_DIR/test_summary.txt"
    fi
}

# Fonction pour afficher le résumé
show_summary() {
    echo ""
    echo -e "${BLUE}📊 Résumé des tests${NC}"
    echo "=================="
    
    if [ -d "$COVERAGE_DIR" ]; then
        echo -e "${GREEN}✅ Couverture de code: $COVERAGE_DIR/index.html${NC}"
    fi
    
    if [ -f "$COVERAGE_REPORT" ]; then
        echo -e "${GREEN}✅ Rapport XML: $COVERAGE_REPORT${NC}"
    fi
    
    if [ -d "$REPORTS_DIR" ]; then
        echo -e "${GREEN}✅ Rapport de tests: $REPORTS_DIR/test_summary.txt${NC}"
    fi
    
    echo ""
    log_success "Tests terminés!"
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
        -c|--no-coverage)
            COVERAGE=false
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -k)
            PATTERN="$2"
            shift 2
            ;;
        -m)
            MARKERS="$2"
            shift 2
            ;;
        -d|--directory)
            TEST_DIR="$2"
            shift 2
            ;;
        -r|--reports)
            REPORTS_DIR="$2"
            shift 2
            ;;
        --unit)
            MARKERS="unit"
            shift
            ;;
        --integration)
            MARKERS="integration"
            shift
            ;;
        --security)
            MARKERS="security"
            shift
            ;;
        --performance)
            MARKERS="performance"
            shift
            ;;
        *)
            log_error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# Exécution principale
main() {
    echo -e "${BLUE}🚀 Démarrage des tests Corporate OS${NC}"
    echo "================================"
    echo ""
    
    # Vérifier les prérequis
    check_prerequisites
    
    # Nettoyer les anciens rapports
    cleanup_reports
    
    # Exécuter les tests
    if run_tests; then
        # Générer les rapports
        generate_reports
        
        # Afficher le résumé
        show_summary
        
        exit 0
    else
        log_error "Échec des tests"
        exit 1
    fi
}

# Exécuter le script principal
main "$@"

