"""
Logique d'export CSV commune à tous les processors.

Fonctions :
- _detect_columns() : Détecte automatiquement les colonnes dans du texte OCR
- export_to_csv() : Exporte les lignes dans un fichier CSV structuré
"""

from pathlib import Path
from typing import List
import re
import pandas as pd  # type: ignore


def detect_columns(lines: List[str]) -> List[List[str]]:
    """Détecte automatiquement les colonnes dans les lignes de texte.
    
    Utilise plusieurs heuristiques pour séparer les colonnes :
    - Espaces multiples (3+ espaces consécutifs)
    - Tabulations
    - Patterns répétitifs de séparation
    
    Returns
    -------
    List[List[str]]
        Liste de lignes, chaque ligne contenant une liste de cellules.
    """
    if not lines:
        return []
    
    structured_data = []
    
    for line in lines:
        # Méthode 1: Split sur espaces multiples (3+ espaces)
        cells = [cell.strip() for cell in line.split('   ') if cell.strip()]
        
        # Si pas assez de colonnes détectées, essaye avec 2+ espaces
        if len(cells) <= 1:
            cells = [cell.strip() for cell in line.split('  ') if cell.strip()]
        
        # Si toujours pas assez, essaye les tabulations
        if len(cells) <= 1:
            cells = [cell.strip() for cell in line.split('\t') if cell.strip()]
        
        # Dernière tentative: détection de patterns numériques/monétaires
        if len(cells) <= 1:
            # Sépare sur les transitions texte -> nombre ou nombre -> texte
            parts = re.split(r'(\s+(?=\d)|\s+(?=[A-Za-z]))', line.strip())
            cells = [part.strip() for part in parts if part.strip() and not part.isspace()]
        
        # Si on a toujours qu'une seule cellule, on la garde telle quelle
        if len(cells) <= 1:
            cells = [line.strip()]
        
        if cells:  # Ignore les lignes vides
            structured_data.append(cells)
    
    # Normalise le nombre de colonnes (complète avec des cellules vides)
    if structured_data:
        max_cols = max(len(row) for row in structured_data)
        for row in structured_data:
            while len(row) < max_cols:
                row.append("")
    
    return structured_data


def export_structured_to_csv(
    table_data: List[List[str]],
    dest_path: Path,
    debug: bool = False,
    metadata: dict = None
) -> None:
    """Écrit une structure de tableau déjà organisée directement dans un CSV.
    
    Utilisé quand on a déjà la structure exacte du tableau (ex: extraction native de Document AI).
    
    Parameters
    ----------
    table_data : List[List[str]]
        Tableau structuré : liste de lignes, chaque ligne contenant une liste de cellules.
    dest_path : Path
        Chemin du fichier CSV de sortie.
    debug : bool
        Si True, génère un fichier .debug.txt avec les données brutes.
    metadata : dict, optional
        Métadonnées du processor utilisé (processor_name, model, tokens, cost, etc.).
    """
    if not table_data:
        raise ValueError("Aucune donnée de tableau à écrire dans le CSV.")
    
    # Normaliser le nombre de colonnes (au cas où certaines lignes sont plus courtes)
    max_cols = max(len(row) for row in table_data)
    for row in table_data:
        while len(row) < max_cols:
            row.append("")
    
    # Création du DataFrame avec colonnes nommées
    columns = [f"Colonne_{i+1}" for i in range(max_cols)]
    df = pd.DataFrame(table_data, columns=columns)
    
    # Sauvegarde du CSV
    df.to_csv(dest_path, index=False, encoding="utf-8")
    
    # Debug
    if debug:
        debug_path = dest_path.with_suffix('.debug.txt')
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write("=== DONNÉES STRUCTURÉES ===\n")
            for i, row in enumerate(table_data):
                f.write(f"{i+1:2d}: {row}\n")
            f.write(f"\n=== INFORMATIONS ===\n")
            f.write(f"Nombre de lignes: {len(table_data)}\n")
            f.write(f"Nombre de colonnes: {max_cols}\n")
            
            # Métadonnées du processor
            if metadata:
                f.write(f"\n=== PROCESSOR ===\n")
                processor_name = metadata.get('processor_name', 'Inconnu')
                f.write(f"Processor: {processor_name}\n")
                
                # Infos spécifiques ChatGPT
                if 'model' in metadata:
                    f.write(f"Modèle: {metadata['model']}\n")
                if 'prompt_tokens' in metadata:
                    f.write(f"Tokens (prompt): {metadata['prompt_tokens']}\n")
                if 'completion_tokens' in metadata:
                    f.write(f"Tokens (completion): {metadata['completion_tokens']}\n")
                if 'total_tokens' in metadata:
                    f.write(f"Tokens (total): {metadata['total_tokens']}\n")
                if 'estimated_cost' in metadata:
                    f.write(f"Coût estimé: ${metadata['estimated_cost']:.4f} USD\n")
                
                # Infos spécifiques Document AI
                if 'processor_id' in metadata:
                    f.write(f"Processor ID: {metadata['processor_id']}\n")
                if 'location' in metadata:
                    f.write(f"Location: {metadata['location']}\n")
            else:
                f.write(f"Source: Extraction native de tableaux\n")


def export_to_csv(
    lines: List[str], 
    dest_path: Path, 
    debug: bool = False,
    metadata: dict = None
) -> None:
    """Écrit les lignes extraites dans un CSV structuré avec détection automatique des colonnes.

    Amélioration par rapport à la version précédente :
    - Détection automatique des séparateurs de colonnes
    - Normalisation du nombre de colonnes
    - Nettoyage des cellules vides
    
    Parameters
    ----------
    lines : List[str]
        Lignes de texte à exporter.
    dest_path : Path
        Chemin du fichier CSV de sortie.
    debug : bool
        Si True, génère un fichier .debug.txt avec les données brutes.
    metadata : dict, optional
        Métadonnées du processor utilisé (processor_name, etc.).
    """
    if not lines:
        raise ValueError("Aucune ligne à écrire dans le CSV.")

    # Détection automatique des colonnes
    structured_data = detect_columns(lines)
    
    if not structured_data:
        raise ValueError("Impossible de structurer les données en colonnes.")
    
    # Création du DataFrame avec colonnes nommées
    max_cols = len(structured_data[0]) if structured_data else 0
    columns = [f"Colonne_{i+1}" for i in range(max_cols)]
    
    df = pd.DataFrame(structured_data, columns=columns)
    
    # Sauvegarde du CSV
    df.to_csv(dest_path, index=False, encoding="utf-8")
    
    # Debug : sauvegarde aussi un fichier texte brut pour comparaison
    if debug:
        debug_path = dest_path.with_suffix('.debug.txt')
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write("=== LIGNES BRUTES ===\n")
            for i, line in enumerate(lines):
                f.write(f"{i+1:2d}: {line}\n")
            f.write("\n=== DONNÉES STRUCTURÉES ===\n")
            for i, row in enumerate(structured_data):
                f.write(f"{i+1:2d}: {row}\n")
            f.write(f"\n=== INFORMATIONS ===\n")
            f.write(f"Nombre de lignes: {len(lines)}\n")
            f.write(f"Nombre de lignes structurées: {len(structured_data)}\n")
            f.write(f"Nombre de colonnes détectées: {max_cols}\n")
            
            # Métadonnées du processor
            if metadata:
                f.write(f"\n=== PROCESSOR ===\n")
                processor_name = metadata.get('processor_name', 'Inconnu')
                f.write(f"Processor: {processor_name}\n")
                
                # Infos additionnelles si disponibles
                if 'model' in metadata:
                    f.write(f"Modèle: {metadata['model']}\n")
                if 'language' in metadata:
                    f.write(f"Langue: {metadata['language']}\n")


