#!/usr/bin/env python3
"""
Script de démarrage pour l'application de gestion des actions
"""

import uvicorn
import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au path Python
sys.path.append(str(Path(__file__).parent))

def main():
    """Fonction principale pour démarrer l'application"""
    print(" Démarrage de l'application de gestion des actions...")
    
    # Configuration par défaut
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f" Serveur accessible sur: http://{host}:{port}")
    print(f" Documentation: http://{host}:{port}/docs")
    print(f" Mode reload: {'Activé' if reload else 'Désactivé'}")
    
    # Démarrer l'application
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main() 