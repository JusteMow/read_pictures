"""
Processor OCR utilisant Google Document AI.

Document AI est spécialisé dans l'analyse de documents structurés (tableaux, formulaires, factures).
Plus adapté que Cloud Vision pour les tableaux comptables.

Fonctions :
- check_document_ai_credentials() : Vérifie les credentials et la config
- DocumentAIProcessor.process_image() : Extraction OCR via Document AI
- DocumentAIProcessor.run() : Pipeline complet OCR + export CSV

🔄 PIPELINE PROCESS_IMAGE :
1. Chargement de l'image en bytes
2. Appel à l'API Document AI (processor configuré)
3. Extraction du texte + structure du document
4. Retour des lignes de texte extraites

Configuration requise (dans .env) :
- GOOGLE_CLOUD_PROJECT_ID : ID du projet Google Cloud
- DOCUMENT_AI_PROCESSOR_ID : ID du processor Document AI (ex: your_processor_id)
- DOCUMENT_AI_LOCATION : Région du processor (ex: eu, us, asia)
- GOOGLE_APPLICATION_CREDENTIALS : Chemin vers le JSON service account
  ou GOOGLE_CLOUD_API_KEY : Clé API (si supporté par Document AI)
"""

import os
from pathlib import Path
from typing import List

from .base_processor import BaseProcessor
from .export_processor import export_to_csv, export_structured_to_csv

try:
    from google.cloud import documentai_v1 as documentai  # type: ignore
    from google.api_core.client_options import ClientOptions  # type: ignore
    DOCUMENTAI_AVAILABLE = True
except ImportError:
    DOCUMENTAI_AVAILABLE = False


def check_document_ai_credentials() -> tuple[str, str, str]:
    """Vérifie que les credentials Document AI sont disponibles.
    
    Returns
    -------
    tuple[str, str, str]
        (project_id, processor_id, location)
    
    Raises
    ------
    RuntimeError
        Si les credentials ou la configuration sont manquants.
    """
    if not DOCUMENTAI_AVAILABLE:
        raise RuntimeError(
            "Package google-cloud-documentai non installé.\n"
            "Installez-le avec : pip install google-cloud-documentai"
        )
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
    location = os.getenv("DOCUMENT_AI_LOCATION", "eu")
    
    if not project_id or not processor_id:
        raise RuntimeError(
            "Configuration Document AI incomplète.\n"
            "Ajoutez ces variables dans le fichier .env :\n"
            "- GOOGLE_CLOUD_PROJECT_ID=your_project_id\n"
            "- DOCUMENT_AI_PROCESSOR_ID=your_processor_id\n"
            "- DOCUMENT_AI_LOCATION=eu\n\n"
            "Et l'une des deux options d'authentification :\n"
            "- GOOGLE_APPLICATION_CREDENTIALS=/chemin/vers/service-account.json\n"
            "  (recommandé, téléchargeable depuis Google Cloud Console)\n"
            "- ou GOOGLE_CLOUD_API_KEY=votre_clé_api\n"
            "  (si supporté par Document AI)"
        )
    
    # Vérification des credentials
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    api_key = os.getenv("GOOGLE_CLOUD_API_KEY")
    
    if not credentials_path and not api_key:
        raise RuntimeError(
            "Credentials Google Cloud manquants.\n"
            "Ajoutez dans .env :\n"
            "- GOOGLE_APPLICATION_CREDENTIALS=/chemin/vers/service-account.json\n"
            "  ou\n"
            "- GOOGLE_CLOUD_API_KEY=votre_clé_api"
        )
    
    if credentials_path and not Path(credentials_path).exists():
        raise RuntimeError(
            f"Fichier de credentials introuvable : {credentials_path}\n"
            "Vérifiez le chemin dans GOOGLE_APPLICATION_CREDENTIALS"
        )
    
    return project_id, processor_id, location


class DocumentAIProcessor(BaseProcessor):
    """Processor OCR utilisant Google Document AI.
    
    Avantages par rapport à Cloud Vision :
    - Compréhension de la structure des documents
    - Meilleure extraction de tableaux
    - Détection des champs de formulaires
    - Analyse de mise en page avancée
    
    Idéal pour : factures, reçus, formulaires, tableaux comptables.
    """

    def __init__(self, debug: bool = True):
        super().__init__(debug=debug)
        
        # !: Vérifie les credentials et récupère la config au démarrage
        self.project_id, self.processor_id, self.location = check_document_ai_credentials()
        
        # Configuration du client Document AI
        opts = ClientOptions(api_endpoint=f"{self.location}-documentai.googleapis.com")
        self.client = documentai.DocumentProcessorServiceClient(client_options=opts)
        
        # Nom complet du processor
        self.processor_name = self.client.processor_path(
            self.project_id, self.location, self.processor_id
        )
        
        if self.debug:
            print(f"Document AI initialisé :")
            print(f"  - Projet : {self.project_id}")
            print(f"  - Processor : {self.processor_id}")
            print(f"  - Région : {self.location}")

    def _extract_tables_from_document(self, document, image_path: Path) -> List[List[List[str]]]:
        """Extrait les tableaux natifs de Document AI avec leur structure.
        
        Parameters
        ----------
        document : documentai.Document
            Document retourné par l'API Document AI.
        image_path : Path
            Chemin de l'image (pour debug).
            
        Returns
        -------
        List[List[List[str]]]
            Liste de tableaux, chaque tableau étant une liste de lignes,
            chaque ligne étant une liste de cellules.
        """
        tables = []
        
        if not document.pages:
            return tables
        
        for page in document.pages:
            if not page.tables:
                continue
                
            for table_idx, table in enumerate(page.tables):
                # Déterminer le nombre de lignes et colonnes
                max_row = 0
                max_col = 0
                
                # Analyser toutes les cellules pour trouver les dimensions
                all_cells = []
                if table.header_rows:
                    for row in table.header_rows:
                        for cell in row.cells:
                            all_cells.append(('header', cell))
                if table.body_rows:
                    for row in table.body_rows:
                        for cell in row.cells:
                            all_cells.append(('body', cell))
                
                for _, cell in all_cells:
                    row_end = cell.layout.text_anchor.text_segments[0].end_index if cell.layout.text_anchor.text_segments else 0
                    col_end = cell.layout.text_anchor.text_segments[0].end_index if cell.layout.text_anchor.text_segments else 0
                    # Document AI donne row_index et col_index
                    if hasattr(cell, 'row_index'):
                        max_row = max(max_row, cell.row_index + cell.row_span)
                    if hasattr(cell, 'col_index'):
                        max_col = max(max_col, cell.col_index + cell.col_span)
                
                # Créer une matrice vide
                table_data = [['' for _ in range(max_col + 1)] for _ in range(max_row + 1)]
                
                # Remplir la matrice avec les cellules
                for cell_type, cell in all_cells:
                    # Extraire le texte de la cellule
                    text_segments = cell.layout.text_anchor.text_segments
                    cell_text = ''
                    for segment in text_segments:
                        start = segment.start_index if hasattr(segment, 'start_index') else 0
                        end = segment.end_index
                        cell_text += document.text[start:end]
                    cell_text = cell_text.strip()
                    
                    # Positionner dans la matrice (gérer colspan/rowspan)
                    if hasattr(cell, 'row_index') and hasattr(cell, 'col_index'):
                        row_idx = cell.row_index
                        col_idx = cell.col_index
                        row_span = cell.row_span if hasattr(cell, 'row_span') else 1
                        col_span = cell.col_span if hasattr(cell, 'col_span') else 1
                        
                        # Remplir toutes les cellules fusionnées
                        for r in range(row_idx, min(row_idx + row_span, len(table_data))):
                            for c in range(col_idx, min(col_idx + col_span, len(table_data[0]))):
                                if r < len(table_data) and c < len(table_data[0]):
                                    table_data[r][c] = cell_text
                
                # Nettoyer les lignes vides
                table_data = [row for row in table_data if any(cell.strip() for cell in row)]
                
                if table_data:
                    tables.append(table_data)
                    
                    if self.debug:
                        print(f"  📊 Tableau {table_idx + 1} : {len(table_data)} lignes × {len(table_data[0]) if table_data else 0} colonnes")
        
        return tables

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
            # Lecture de l'image
            with open(image_path, 'rb') as image_file:
                image_content = image_file.read()
            
            # Détection du type MIME
            suffix = image_path.suffix.lower()
            mime_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.bmp': 'image/bmp',
                '.tiff': 'image/tiff',
                '.tif': 'image/tiff',
                '.pdf': 'application/pdf',
            }
            mime_type = mime_type_map.get(suffix, 'image/jpeg')
            
            # Préparation de la requête
            raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)
            request = documentai.ProcessRequest(name=self.processor_name, raw_document=raw_document)
            
            # Appel à l'API Document AI
            if self.debug:
                print(f"Envoi de {image_path.name} à Document AI...")
            
            result = self.client.process_document(request=request)
            document = result.document
            
            if self.debug:
                print(f"✅ Document traité : {len(document.text)} caractères extraits")
                print(f"   Confiance moyenne : {document.pages[0].layout.confidence:.2%}" if document.pages else "")
            
            # !: Tentative d'extraction des tableaux natifs en priorité
            tables = self._extract_tables_from_document(document, image_path)
            
            # Stocker les tableaux pour le run() qui va les utiliser
            self._last_extracted_tables = tables if tables else None
            
            # Extraction du texte (fallback si pas de tableaux)
            full_text = document.text
            lines = [line.strip() for line in full_text.splitlines() if line.strip()]
            
            # Sauvegarde debug
            if self.debug:
                debug_dir = image_path.parent / "debug"
                debug_dir.mkdir(exist_ok=True)
                
                # Texte complet
                with open(debug_dir / f"{image_path.stem}_document_ai.txt", "w", encoding="utf-8") as f:
                    f.write("=== TEXTE COMPLET ===\n")
                    f.write(full_text)
                    f.write("\n\n=== LIGNES EXTRAITES ===\n")
                    for i, line in enumerate(lines, 1):
                        f.write(f"{i:3d}: {line}\n")
                    
                    # Infos supplémentaires
                    f.write("\n\n=== INFORMATIONS DOCUMENT ===\n")
                    f.write(f"Nombre de pages : {len(document.pages)}\n")
                    f.write(f"Nombre de lignes : {len(lines)}\n")
                    f.write(f"Nombre de caractères : {len(full_text)}\n")
                    
                    # Affichage des tableaux détectés
                    if tables:
                        f.write(f"\n=== TABLEAUX EXTRAITS ===\n")
                        f.write(f"Nombre de tableaux : {len(tables)}\n")
                        for idx, table_data in enumerate(tables, 1):
                            f.write(f"\nTableau {idx} : {len(table_data)} lignes × {len(table_data[0]) if table_data else 0} colonnes\n")
                            for row_idx, row in enumerate(table_data[:5]):  # Afficher les 5 premières lignes
                                f.write(f"  Ligne {row_idx + 1}: {row}\n")
                            if len(table_data) > 5:
                                f.write(f"  ... ({len(table_data) - 5} lignes supplémentaires)\n")
            
            if self.debug:
                if tables:
                    print(f"📊 {len(tables)} tableau(x) extrait(s)")
                else:
                    print(f"📄 {len(lines)} lignes extraites (aucun tableau détecté)")
            
            return lines
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors du traitement de {image_path} avec Document AI: {e}") from e

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

            # Initialiser l'attribut pour stocker les tableaux
            self._last_extracted_tables = None
            
            lines = self.process_image(image_path)

            csv_path = output_dir / f"{image_path.stem}.csv"
            
            # Prépare les métadonnées pour le fichier debug
            metadata = {
                'processor_name': 'Google Document AI',
                'processor_id': self.processor_id,
                'location': self.location
            }
            
            # !: Si des tableaux ont été extraits, on les utilise directement
            if self._last_extracted_tables:
                # Exporter tous les tableaux (si plusieurs, on prend le premier pour l'instant)
                # TODO: gérer plusieurs tableaux par image (export en plusieurs CSV ou fusion)
                table_data = self._last_extracted_tables[0]
                export_structured_to_csv(table_data, csv_path, debug=self.debug, metadata=metadata)
            else:
                # Fallback : export texte avec détection de colonnes
                export_to_csv(lines, csv_path, debug=self.debug, metadata=metadata)
            
            return csv_path
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors du pipeline complet pour {image_path}: {e}") from e

