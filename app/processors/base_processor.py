"""
Classe abstraite pour tous les processors OCR.

Définit l'interface commune que doivent implémenter tous les processors.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class BaseProcessor(ABC):
    """Classe abstraite pour les processors OCR.
    
    Tout processor doit implémenter :
    - process_image() : extrait le texte d'une image
    - run() : pipeline complet (OCR + export CSV)
    """

    def __init__(self, debug: bool = True):
        self.debug = debug

    @abstractmethod
    def process_image(self, image_path: Path) -> List[str]:
        """Extrait les lignes de texte d'une image.
        
        Parameters
        ----------
        image_path : Path
            Chemin de l'image à traiter.
            
        Returns
        -------
        List[str]
            Liste des lignes de texte extraites.
        """
        pass

    @abstractmethod
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
        pass


