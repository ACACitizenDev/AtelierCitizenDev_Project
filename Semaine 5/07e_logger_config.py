import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Création du dossier de logs s'il n'existe pas
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR).lower() in ['semaine 5', 'semaine_5'] else SCRIPT_DIR
LOG_DIR = os.path.join(PARENT_DIR, 'Base de donnée', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"pipeline_bancaire_{datetime.now().strftime('%Y%m')}.log")

def setup_logger():
    """Configure un logger professionnel avec sortie console et fichier tournant."""
    logger = logging.getLogger("BanqueGeneveLogger")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # Format des logs structuré conforme aux normes d'audit
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 1. Handler Fichier (Tournant 5 Mo max, conserve 3 sauvegardes)
        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # 2. Handler Console (Terminal)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger, LOG_FILE

logger, CURRENT_LOG_PATH = setup_logger()

if __name__ == '__main__':
    logger.info("▶️ Test initial du logger structuré.")
    logger.warning("⚠️ Message d'avertissement de test.")
    logger.error("❌ Message d'erreur simulé.")