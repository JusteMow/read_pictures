"""
Processor OCR utilisant Tesseract (OCR local gratuit).

Fonctions :
- check_tesseract_installation() : Vérifie que Tesseract est installé
- TesseractProcessor.process_image() : Extraction OCR avec prétraitement optimisé
- TesseractProcessor.run() : Pipeline complet OCR + export CSV

🔄 PIPELINE PROCESS_IMAGE :
1. Chargement image + redimensionnement si nécessaire (min 1000px)
2. Prétraitement : grayscale → CLAHE → débruitage → binarisation (Otsu + Adaptive)
3. Test de plusieurs configs Tesseract (PSM 6/4/3/11/12) sur les 2 seuils
4. Sélection du meilleur résultat (confiance maximale)
5. Retour des lignes de texte extraites
"""

from pathlib import Path
from typing import List

import cv2  # type: ignore
import numpy as np  # type: ignore
import pytesseract  # type: ignore

from .base_processor import BaseProcessor
from .export_processor import export_to_csv

# !: pytesseract nécessite que Tesseract OCR soit installé sur le système et que son binaire soit accessible via PATH.
# !: Pour Windows, installer https://github.com/tesseract-ocr/tesseract/wiki et ajouter le chemin du dossier d'installation/bin.


def check_tesseract_installation() -> None:
    """Vérifie que Tesseract est installé et accessible."""
    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        raise RuntimeError(
            "Tesseract n'est pas installé ou n'est pas dans le PATH.\n"
            "1. Téléchargez Tesseract depuis : https://github.com/UB-Mannheim/tesseract/wiki\n"
            "2. Installez-le en cochant 'Add to PATH'\n"
            "3. Redémarrez l'application"
        ) from e


class TesseractProcessor(BaseProcessor):
    """Processor OCR utilisant Tesseract.
    
    Amélioration du prétraitement pour les tableaux comptables.
    Plusieurs configurations Tesseract testées automatiquement.
    """

    def __init__(self, lang: str = "fra", debug: bool = True):
        super().__init__(debug=debug)
        check_tesseract_installation()  # !: Vérifie l'installation au démarrage
        self.lang = lang

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
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                raise FileNotFoundError(f"Impossible de lire {image_path}")

            # Redimensionnement si l'image est trop petite (améliore l'OCR)
            height, width = img.shape[:2]
            if height < 1000 or width < 1000:
                scale = max(1000 / height, 1000 / width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Amélioration du contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
            
            # Débruitage
            gray = cv2.medianBlur(gray, 3)
            
            # Binarisation améliorée - teste plusieurs méthodes
            # Méthode 1: Otsu (souvent meilleure pour les documents)
            _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Méthode 2: Adaptive (pour les éclairages non uniformes)
            thresh2 = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            if self.debug:
                debug_dir = image_path.parent / "debug"
                debug_dir.mkdir(exist_ok=True)
                cv2.imwrite(str(debug_dir / f"{image_path.stem}_original.png"), img)
                cv2.imwrite(str(debug_dir / f"{image_path.stem}_gray.png"), gray)
                cv2.imwrite(str(debug_dir / f"{image_path.stem}_otsu.png"), thresh1)
                cv2.imwrite(str(debug_dir / f"{image_path.stem}_adaptive.png"), thresh2)

            # Test plusieurs configurations Tesseract
            configs = [
                "--oem 3 --psm 6",   # Block de texte uniforme
                "--oem 3 --psm 4",   # Colonne unique de texte
                "--oem 3 --psm 3",   # Page complète auto
                "--oem 3 --psm 11",  # Page clairsemée
                "--oem 3 --psm 12",  # Page clairsemée avec OSD
            ]
            
            best_result = []
            best_confidence = 0
            
            for i, config in enumerate(configs):
                for j, thresh in enumerate([thresh1, thresh2]):
                    try:
                        # Extraction avec données de confiance
                        data = pytesseract.image_to_data(
                            thresh, lang=self.lang, config=config, output_type=pytesseract.Output.DICT
                        )
                        
                        # Calcul de la confiance moyenne
                        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                        
                        # Extraction du texte
                        text = pytesseract.image_to_string(thresh, lang=self.lang, config=config)
                        lines = [line.strip() for line in text.splitlines() if line.strip()]
                        
                        if self.debug:
                            print(f"Config {i+1}, Seuil {j+1}: {len(lines)} lignes, confiance: {avg_confidence:.1f}%")
                            debug_dir = image_path.parent / "debug"
                            with open(debug_dir / f"{image_path.stem}_result_{i+1}_{j+1}.txt", "w", encoding="utf-8") as f:
                                f.write(f"Config: {config}\n")
                                f.write(f"Confiance moyenne: {avg_confidence:.1f}%\n")
                                f.write(f"Nombre de lignes: {len(lines)}\n\n")
                                f.write(text)
                        
                        # Garde le meilleur résultat
                        if avg_confidence > best_confidence and lines:
                            best_confidence = avg_confidence
                            best_result = lines
                            
                    except Exception as e:
                        if self.debug:
                            print(f"Erreur config {i+1}, seuil {j+1}: {e}")

            if self.debug:
                print(f"Meilleur résultat: {len(best_result)} lignes, confiance: {best_confidence:.1f}%")
            
            return best_result
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors du traitement de {image_path}: {e}") from e

    def run(self, image_path: Path, output_dir: Path | None = None) -> Path:
        """Pipeline complet : OCR + export CSV.

        Parameters
        ----------
        image_path : Path
            Image à traiter.
        output_dir : Path | None, optional
            Répertoire de sortie. S'il est None, on utilise le dossier de
            l'image ou son sous-dossier "output".

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
                'processor_name': 'Tesseract OCR',
                'language': self.lang
            }

            csv_path = output_dir / f"{image_path.stem}.csv"
            export_to_csv(lines, csv_path, debug=self.debug, metadata=metadata)
            return csv_path
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors du pipeline complet pour {image_path}: {e}") from e


