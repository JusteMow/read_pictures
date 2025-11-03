#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Processor OCR utilisant l'API ChatGPT (GPT-4o-mini with Vision).

ChatGPT Vision est particulièrement performant pour :
- Extraction de tableaux complexes
- Compréhension du contexte et de la structure
- Génération directe de CSV bien formaté

Fonctions :
- check_chatgpt_credentials() : Vérifie la présence de OPENAI_API_KEY
- ChatGPTProcessor.process_image() : Extraction CSV via ChatGPT Vision
- ChatGPTProcessor.run() : Pipeline complet OCR + export CSV

🔄 PIPELINE PROCESS_IMAGE :
1. Chargement de l'image en base64
2. Appel à l'API ChatGPT (gpt-4o-mini avec vision)
3. Extraction et parsing du CSV retourné
4. Retour d'une structure de tableau List[List[str]]

Configuration requise (dans .env ou variables d'environnement) :
- OPENAI_API_KEY : Clé API OpenAI (ex: sk-...)
- COST_PER_1M_INPUT : Coût par 1M tokens input (optionnel, défaut 0.60 USD)
- COST_PER_1M_OUTPUT : Coût par 1M tokens output (optionnel, défaut 2.40 USD)
"""

import os
import io
import csv
import re
import sys
import base64
import logging
from pathlib import Path
from typing import List, Optional, Dict

from PIL import Image

from .base_processor import BaseProcessor
from .export_processor import export_structured_to_csv

# SDK OpenAI v1
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# -------------- Configuration --------------

DEFAULT_MODEL = "gpt-4o-mini"

CSV_HEADER = ["Reference", "Facture", "Numero", "Beneficiaire", "Date", "Montant", "Total"]

SYSTEM_PROMPT = (
    "Tu es un extracteur de tableaux bancaires. "
    "À partir d'une image contenant une liste de virements pour 'Dr PC Bordeaux', "
    "retourne STRICTEMENT un CSV avec séparateur virgule, en UTF-8, sans texte additionnel.\n"
    "En-tête EXACTE (1ère ligne) : Reference,Facture,Numero,Beneficiaire,Date,Montant,Total\n"
    "- Beneficiaire = 'Dr PC Bordeaux' si visible (sinon laisse vide)\n"
    "- Date au format JJ/MM/AAAA\n"
    "- Montant et Total en décimal avec point (ex: 63.00)\n"
    "- Si un champ est manquant: laisse vide mais conserve les virgules\n"
    "- Pas d'explication ni de code, CSV uniquement."
)

# -------------- Utils --------------

def check_chatgpt_credentials() -> str:
    """
    Vérifie que OPENAI_API_KEY est configurée.
    
    Returns
    -------
    str
        La clé API OpenAI.
        
    Raises
    ------
    ValueError
        Si la clé n'est pas trouvée dans l'environnement.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "❌ OPENAI_API_KEY manquant dans l'environnement.\n\n"
            "Pour utiliser ChatGPT Processor, configure :\n"
            "  OPENAI_API_KEY=sk-...\n\n"
            "Obtiens une clé sur : https://platform.openai.com/api-keys"
        )
    
    return api_key


def b64_of_image(img: Image.Image) -> str:
    """Encode une image Pillow en base64 PNG."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def read_image_as_b64(path: Path) -> str:
    """
    Lit une image et retourne une data URL base64 (PNG).
    
    Parameters
    ----------
    path : Path
        Chemin de l'image.
        
    Returns
    -------
    str
        Data URL au format "data:image/png;base64,..."
    """
    img = Image.open(path).convert("RGB")
    return f"data:image/png;base64,{b64_of_image(img)}"


def post_vision_csv(
    client: OpenAI, 
    model: str, 
    image_b64: str, 
    user_prompt: Optional[str] = None
) -> Dict:
    """
    Envoie une image au modèle ChatGPT et récupère la réponse (CSV).
    
    Parameters
    ----------
    client : OpenAI
        Client OpenAI initialisé.
    model : str
        Nom du modèle (ex: gpt-4o-mini).
    image_b64 : str
        Data URL base64 de l'image.
    user_prompt : str, optional
        Prompt utilisateur additionnel.
        
    Returns
    -------
    Dict
        Objet réponse du SDK OpenAI.
    """
    content = [
        {"type": "text", "text": (user_prompt or "Extrait le tableau en CSV, selon tes instructions.")},
        {"type": "image_url", "image_url": {"url": image_b64}}
    ]

    # Chat Completions (compatible vision)
    return client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
    )


def sanitize_csv_text(txt: str) -> str:
    """
    Nettoyage minimal: enlève BOM/markdown/accroches accidentelles, normalise fins de lignes.
    Reconvertit ';' en ',' si nécessaire.
    
    Parameters
    ----------
    txt : str
        Texte CSV brut de ChatGPT.
        
    Returns
    -------
    str
        CSV nettoyé.
    """
    if txt is None:
        return ""

    # Enlève balises code éventuelles
    txt = txt.strip()
    txt = re.sub(r"^```[a-zA-Z]*\n?", "", txt)
    txt = re.sub(r"\n?```$", "", txt)
    txt = txt.replace("\r\n", "\n").replace("\r", "\n").strip()

    # Si ';' semble le séparateur, on remplace par ','
    lines = [l for l in txt.split("\n") if l.strip()]
    semi = sum(l.count(";") for l in lines)
    comma = sum(l.count(",") for l in lines)
    if semi > comma:
        txt = txt.replace(";", ",")

    # Supprime doublons d'entête si le modèle l'a remis plusieurs fois
    out_lines = []
    seen_header = False
    for l in lines:
        if re.match(r"(?i)^reference,?facture,?numero,?beneficiaire,?date,?montant,?total$", l.replace(" ", "")):
            if seen_header:
                continue
            seen_header = True
            out_lines.append(",".join(CSV_HEADER))
        else:
            out_lines.append(l)
    
    # S'il n'a jamais donné d'en-tête (rare), on le préfixe
    if out_lines and not re.match(r"(?i)^reference,facture,numero,beneficiaire,date,montant,total$", out_lines[0].replace(" ", "")):
        out_lines.insert(0, ",".join(CSV_HEADER))

    return "\n".join(out_lines).strip() + "\n"


def parse_csv_to_table(csv_text: str) -> List[List[str]]:
    """
    Parse un texte CSV en structure de tableau.
    
    Parameters
    ----------
    csv_text : str
        Texte CSV (avec header).
        
    Returns
    -------
    List[List[str]]
        Structure de tableau (header + lignes).
    """
    f = io.StringIO(csv_text)
    reader = csv.reader(f)
    table = []
    
    for row in reader:
        if not row or all(not c.strip() for c in row):
            continue
        # Normalise le nombre de colonnes
        row = (row + [""] * len(CSV_HEADER))[:len(CSV_HEADER)]
        table.append(row)
    
    return table


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """
    Estime le coût en USD selon les variables d'environnement.
    
    Parameters
    ----------
    prompt_tokens : int
        Nombre de tokens dans le prompt.
    completion_tokens : int
        Nombre de tokens dans la réponse.
        
    Returns
    -------
    float
        Coût estimé en USD.
    """
    cost_in = float(os.getenv("COST_PER_1M_INPUT", "0.60"))
    cost_out = float(os.getenv("COST_PER_1M_OUTPUT", "2.40"))
    return (prompt_tokens / 1_000_000) * cost_in + (completion_tokens / 1_000_000) * cost_out


# -------------- Processor --------------

class ChatGPTProcessor(BaseProcessor):
    """Processor OCR utilisant ChatGPT Vision (GPT-4o-mini).
    
    Avantages :
    - Excellente compréhension du contexte
    - Génération directe de CSV structuré
    - Pas de preprocessing nécessaire
    - Gestion native des tableaux complexes
    
    Idéal pour : tableaux bancaires, factures complexes, documents avec mise en page variable.
    """

    def __init__(self, debug: bool = True, model: str = DEFAULT_MODEL):
        """
        Initialise le processor ChatGPT.
        
        Parameters
        ----------
        debug : bool
            Active les logs de debug.
        model : str
            Modèle à utiliser (défaut: gpt-4o-mini).
        """
        super().__init__(debug=debug)
        
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "Le SDK OpenAI n'est pas installé.\n"
                "Installe-le avec : pip install openai>=1.0"
            )
        
        # !: Vérifie les credentials au démarrage
        self.api_key = check_chatgpt_credentials()
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        
        # Stockage des dernières métadonnées d'appel (pour export debug)
        self._last_prompt_tokens = 0
        self._last_completion_tokens = 0
        self._last_total_tokens = 0
        self._last_cost = 0.0
        
        if self.debug:
            print(f"ChatGPT Processor initialisé :")
            print(f"  - Modèle : {self.model}")
            print(f"  - API Key : {self.api_key[:10]}...{self.api_key[-4:]}")

    def process_image(self, image_path: Path) -> List[str]:
        """
        Extrait les lignes de texte d'une image via ChatGPT Vision.
        
        Note : ChatGPT retourne directement un CSV structuré.
        Cette méthode retourne les lignes brutes du CSV (sans parsing).
        
        Parameters
        ----------
        image_path : Path
            Chemin de l'image à traiter.
            
        Returns
        -------
        List[str]
            Liste des lignes de texte CSV (brutes).
            
        Raises
        ------
        Exception
            Si l'appel à l'API échoue.
        """
        try:
            # Charge l'image en base64
            image_b64 = read_image_as_b64(image_path)
            
            if self.debug:
                print(f"Appel ChatGPT pour {image_path.name}...")
            
            # Appel à l'API
            resp = post_vision_csv(self.client, self.model, image_b64)
            
            # Extraction du contenu
            content = resp.choices[0].message.content
            csv_text = sanitize_csv_text(content or "")
            
            # Récupération et stockage des tokens/coût
            usage = getattr(resp, "usage", None) or {}
            self._last_prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
            self._last_completion_tokens = getattr(usage, "completion_tokens", 0) or 0
            self._last_total_tokens = getattr(usage, "total_tokens", 0) or (self._last_prompt_tokens + self._last_completion_tokens)
            self._last_cost = estimate_cost(self._last_prompt_tokens, self._last_completion_tokens)
            
            # Logs de debug sur les tokens
            if self.debug:
                print(f"  ✓ Tokens: prompt={self._last_prompt_tokens}, completion={self._last_completion_tokens}, total={self._last_total_tokens}")
                print(f"  ✓ Coût estimé: ${self._last_cost:.4f} USD")
            
            # Retourne les lignes brutes
            lines = [l for l in csv_text.split("\n") if l.strip()]
            return lines
            
        except Exception as e:
            logger.error(f"Erreur ChatGPT pour {image_path.name}: {e}")
            raise

    def run(self, image_path: Path, output_dir: Path | None = None) -> Path:
        """
        Pipeline complet : OCR via ChatGPT + export CSV.
        
        Parameters
        ----------
        image_path : Path
            Image à traiter.
        output_dir : Path | None, optional
            Répertoire de sortie. Si None, utilise le répertoire de l'image.
            
        Returns
        -------
        Path
            Chemin du fichier CSV généré.
        """
        try:
            # Définit le répertoire de sortie
            if output_dir is None:
                output_dir = image_path.parent / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Appel ChatGPT pour extraction
            lines = self.process_image(image_path)
            
            if not lines:
                raise ValueError(f"Aucune donnée extraite de {image_path.name}")
            
            # Parse le CSV en structure de tableau
            csv_text = "\n".join(lines)
            table_data = parse_csv_to_table(csv_text)
            
            if not table_data:
                raise ValueError(f"Impossible de parser le CSV de {image_path.name}")
            
            # Prépare les métadonnées pour le fichier debug
            metadata = {
                'processor_name': 'ChatGPT Vision',
                'model': self.model,
                'prompt_tokens': self._last_prompt_tokens,
                'completion_tokens': self._last_completion_tokens,
                'total_tokens': self._last_total_tokens,
                'estimated_cost': self._last_cost
            }
            
            # Export vers CSV
            csv_path = output_dir / f"{image_path.stem}.csv"
            export_structured_to_csv(table_data, csv_path, debug=self.debug, metadata=metadata)
            
            if self.debug:
                print(f"✓ CSV généré : {csv_path}")
            
            return csv_path
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de {image_path.name}: {e}")
            raise



