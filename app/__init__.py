"""
Application ReadPicture - OCR de tableaux.

Au démarrage, charge les variables d'environnement depuis .env
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# !: Charge le .env au démarrage de l'app pour avoir accès aux credentials Google Cloud
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Si .env n'existe pas, on continue quand même (Tesseract fonctionnera)
    pass
