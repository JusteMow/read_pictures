"""
Processor OCR utilisant Google Cloud Vision API.

Fonctions :
- check_google_cloud_credentials() : Vérifie que les credentials sont disponibles
- GoogleCloudProcessor.process_image() : Extraction OCR via Google Cloud Vision
- GoogleCloudProcessor.run() : Pipeline complet OCR + export CSV

🔄 PIPELINE PROCESS_IMAGE :
1. Chargement de l'image en bytes
2. Appel à l'API Google Cloud Vision (TEXT_DETECTION)
3. Extraction des lignes de texte depuis la réponse
4. Retour des lignes de texte extraites

Note : Nécessite une clé API Google Cloud ou un fichier de service account.
Configuration via variables d'environnement (.env) :
- GOOGLE_CLOUD_API_KEY : Clé API simple (recommandé pour débuter)
- ou GOOGLE_APPLICATION_CREDENTIALS : Chemin vers le JSON de service account
"""

import os
from pathlib import Path
from typing import List

from .base_processor import BaseProcessor
from .export_processor import export_to_csv

# #TODO: À implémenter une fois les credentials Google Cloud disponibles
# from google.cloud import vision  # type: ignore


def check_google_cloud_credentials() -> None:
    """Vérifie que les credentials Google Cloud sont disponibles."""
    # Méthode 1 : Clé API simple (via .env)
    api_key = os.getenv("GOOGLE_CLOUD_API_KEY")
    
    # Méthode 2 : Service account JSON
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not api_key and not credentials_path:
        raise RuntimeError(
            "Credentials Google Cloud manquants.\n"
            "Configurez l'une de ces variables dans le fichier .env :\n"
            "- GOOGLE_CLOUD_API_KEY=votre_clé_api\n"
            "- GOOGLE_APPLICATION_CREDENTIALS=/chemin/vers/service-account.json\n\n"
            "Pour obtenir une clé API :\n"
            "1. https://console.cloud.google.com/\n"
            "2. APIs & Services → Credentials\n"
            "3. Create Credentials → API Key\n"
            "4. Enable 'Cloud Vision API'"
        )
    
    if credentials_path and not Path(credentials_path).exists():
        raise RuntimeError(
            f"Fichier de credentials introuvable : {credentials_path}\n"
            "Vérifiez le chemin dans GOOGLE_APPLICATION_CREDENTIALS"
        )


class GoogleCloudProcessor(BaseProcessor):
    """Processor OCR utilisant Google Cloud Vision API.
    
    Avantages :
    - Meilleure précision que Tesseract
    - Détection automatique de langue
    - Gestion des rotations et perspectives
    - Structure de document préservée
    """

    def __init__(self, debug: bool = True):
        super().__init__(debug=debug)
        check_google_cloud_credentials()  # !: Vérifie les credentials au démarrage
        
        # #TODO: Initialiser le client Google Cloud Vision une fois la lib installée
        # self.client = vision.ImageAnnotatorClient()

    def process_image(self, image_path: Path) -> List[str]:
        """Lit une image et renvoie une liste de chaînes correspondant aux lignes détectées.

        Parameters
        ----------
        image_path : Path
            Chemin de l'image à traiter.

        Returns
        -------
        List[str]
            Liste des lignes de texte extraites.
        """
        # #TODO: Implémenter l'appel à Google Cloud Vision API
        
        raise NotImplementedError(
            "Google Cloud Vision API n'est pas encore implémenté.\n"
            "En attente de la configuration des credentials et de l'installation de google-cloud-vision.\n"
            "Pour l'instant, utilisez TesseractProcessor."
        )
        
        # Code de référence pour l'implémentation future :
        """
        try:
            # Lecture de l'image
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Appel à l'API (TEXT_DETECTION pour OCR simple, DOCUMENT_TEXT_DETECTION pour documents structurés)
            response = self.client.text_detection(image=image)
            
            if response.error.message:
                raise RuntimeError(f"Erreur API Google Cloud Vision: {response.error.message}")
            
            # Extraction du texte
            texts = response.text_annotations
            
            if not texts:
                return []
            
            # Le premier élément contient tout le texte, on le split en lignes
            full_text = texts[0].description
            lines = [line.strip() for line in full_text.splitlines() if line.strip()]
            
            if self.debug:
                print(f"Google Cloud Vision: {len(lines)} lignes extraites")
                debug_dir = image_path.parent / "debug"
                debug_dir.mkdir(exist_ok=True)
                with open(debug_dir / f"{image_path.stem}_google_cloud.txt", "w", encoding="utf-8") as f:
                    f.write(full_text)
            
            return lines
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors du traitement de {image_path}: {e}") from e
        """

    def run(self, image_path: Path, output_dir: Path | None = None) -> Path:
        """Pipeline complet : OCR + export CSV.

        Parameters
        ----------
        image_path : Path
            Image à traiter.
        output_dir : Path | None, optional
            Répertoire de sortie.

        Returns
        -------
        Path
            Chemin du fichier CSV généré.
        """
        try:
            if output_dir is None:
                output_dir = image_path.parent / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            lines = self.process_image(image_path)

            # Prépare les métadonnées pour le fichier debug
            metadata = {
                'processor_name': 'Google Cloud Vision'
            }

            csv_path = output_dir / f"{image_path.stem}.csv"
            export_to_csv(lines, csv_path, debug=self.debug, metadata=metadata)
            return csv_path
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors du pipeline complet pour {image_path}: {e}") from e


