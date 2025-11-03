# Documentation ReadPicture

## 📋 Vue d'ensemble

Application OCR pour la transcription de tableaux et documents en CSV.

**Architecture modulaire** :
- `main.py` : Point d'entrée
- `app/gui.py` : Interface graphique Tkinter
- `app/processors/` : Modules OCR et export

**Processors disponibles** :
- **TesseractProcessor** : OCR local gratuit
- **GoogleCloudProcessor** : OCR via Google Cloud Vision API (générique)
- **DocumentAIProcessor** : OCR via Google Document AI (spécialisé tableaux et documents structurés)
- **ChatGPTProcessor** : OCR via ChatGPT Vision (GPT-4o-mini, très performant pour tableaux complexes) ⭐ **RECOMMANDÉ**

---

## 🔧 Architecture Processors

```
app/processors/
├─ base_processor.py          # Classe abstraite
├─ tesseract_processor.py     # OCR Tesseract
├─ google_cloud_processor.py  # OCR Google Cloud Vision
├─ document_ai_processor.py   # OCR Document AI (tableaux)
├─ chatgpt_processor.py       # OCR ChatGPT Vision (⭐ performant)
└─ export_processor.py        # Export CSV commun
```

### BaseProcessor (classe abstraite)

**Méthodes à implémenter** :
- `process_image(image_path) -> List[str]` : Extrait les lignes de texte
- `run(image_path, output_dir) -> Path` : Pipeline complet OCR + export CSV

### TesseractProcessor

**Pipeline process_image()** :
1. Chargement + redimensionnement si < 1000px
2. Prétraitement : grayscale → CLAHE → débruitage → binarisation (Otsu + Adaptive)
3. Test de 10 configs (5 PSM × 2 seuils)
4. Sélection du meilleur résultat (confiance max)
5. Retour des lignes de texte

**Configs Tesseract testées** :
- PSM 6 : Bloc de texte uniforme
- PSM 4 : Colonne unique
- PSM 3 : Page complète auto
- PSM 11/12 : Page clairsemée

### GoogleCloudProcessor

**Pipeline process_image()** :
1. Chargement image en bytes
2. Appel API Google Cloud Vision (TEXT_DETECTION)
3. Extraction des lignes depuis la réponse
4. Retour des lignes de texte

**Configuration requise** (dans `.env`) :
- `GOOGLE_CLOUD_API_KEY` : Clé API simple
- ou `GOOGLE_APPLICATION_CREDENTIALS` : Chemin vers JSON service account

### DocumentAIProcessor

**Pipeline process_image()** :
1. Chargement image en bytes + détection type MIME
2. Appel API Document AI (processor configuré)
3. Extraction du texte + structure du document
4. Détection optionnelle des tableaux
5. Retour des lignes de texte

**Avantages vs Cloud Vision** :
- Compréhension de la structure des documents
- Meilleure extraction de tableaux
- Détection des champs de formulaires
- Analyse de mise en page avancée

**Configuration requise** (dans `.env`) :
- `GOOGLE_CLOUD_PROJECT_ID` : ID du projet Google Cloud (ex: 123456789012)
- `DOCUMENT_AI_PROCESSOR_ID` : ID du processor Document AI (ex: your_processor_id)
- `DOCUMENT_AI_LOCATION` : Région du processor (ex: eu, us, asia)
- `GOOGLE_APPLICATION_CREDENTIALS` : Chemin vers JSON service account (OBLIGATOIRE pour Document AI)

### ChatGPTProcessor (⭐ RECOMMANDÉ POUR TABLEAUX COMPLEXES)

**Pipeline process_image()** :
1. Chargement image → conversion base64 PNG
2. Appel API ChatGPT (GPT-4o-mini avec vision)
3. Parsing et nettoyage du CSV retourné
4. Retour d'une structure List[List[str]] (tableau structuré)

**Pipeline run()** :
1. process_image() → récupère le tableau structuré
2. export_structured_to_csv() → génère le CSV final
3. Logs de tokens consommés et coût estimé

**Avantages** :
- Excellente compréhension du contexte et de la structure
- Génération directe de CSV bien formaté
- Pas de preprocessing nécessaire
- Très performant sur tableaux bancaires complexes

**Configuration requise** (dans `.env`) :
- `OPENAI_API_KEY` : Clé API OpenAI (ex: sk-proj-...)
- `COST_PER_1M_INPUT` (optionnel) : Coût par 1M tokens input (défaut 0.60 USD)
- `COST_PER_1M_OUTPUT` (optionnel) : Coût par 1M tokens output (défaut 2.40 USD)

### ExportProcessor (fonctions utilitaires)

**detect_columns(lines)** :
- Détecte automatiquement les colonnes (espaces multiples, tabs, patterns numériques)
- Normalise le nombre de colonnes

**export_to_csv(lines, dest_path, debug)** :
- Utilise detect_columns()
- Crée un DataFrame pandas
- Export en CSV avec colonnes nommées (Colonne_1, Colonne_2...)
- Génère un fichier .debug.txt si debug=True

---

## 🖥️ GUI (gui.py)

**Composants** :
- Radio buttons : Sélection du processor (Tesseract / Google Cloud Vision / Document AI / ChatGPT Vision)
- Bouton "Choisir image(s)" : Sélection multi-fichiers
- Liste des fichiers sélectionnés
- Bouton "Transcrire" : Lance le traitement
- Zone de logs : Affiche les résultats

**Pipeline transcription** :
```
_on_transcribe()
├─> current_processor.run(image_path) pour chaque image
├─> Affichage des résultats dans les logs
└─> MessageBox de confirmation
```

**Gestion des erreurs** :
- Si Google Cloud ou Document AI échoue (credentials manquants) → fallback automatique sur Tesseract
- Si package manquant (ImportError) → fallback sur Tesseract avec message d'alerte
- Si NotImplementedError → fallback sur Tesseract avec message d'alerte

---

## 🚀 Installation & Configuration

### 1. Dépendances Python

```bash
pip install -r requirements.txt
```

**Packages** :
- opencv-python : Traitement d'image
- pytesseract : OCR Tesseract
- pillow : Manipulation d'images
- pandas : Export CSV
- python-dotenv : Gestion des variables d'environnement
- google-cloud-vision : API Google Cloud Vision
- google-cloud-documentai : API Google Document AI
- openai>=1.0 : API ChatGPT Vision

### 2. Tesseract OCR (requis)

**Windows** :
1. Télécharger : https://github.com/UB-Mannheim/tesseract/wiki
2. Installer en cochant "Add to PATH"
3. Redémarrer l'application

### 3. Google Document AI (recommandé pour tableaux)

**Configuration obligatoire** :

1. **Créer un processor Document AI** :
   - https://console.cloud.google.com/ai/document-ai
   - Create Processor → "Document OCR"
   - Noter l'ID du processor (ex: your_processor_id) et la région (ex: eu)

2. **Créer un Service Account** (obligatoire) :
   - https://console.cloud.google.com/iam-admin/serviceaccounts
   - Create Service Account → Donner les permissions Document AI
   - Actions → Manage Keys → Add Key → Create new key → JSON
   - Télécharger le fichier JSON

3. **Configurer le `.env`** :
```bash
GOOGLE_CLOUD_PROJECT_ID=your_project_id
DOCUMENT_AI_PROCESSOR_ID=your_processor_id
DOCUMENT_AI_LOCATION=eu
GOOGLE_APPLICATION_CREDENTIALS=C:\chemin\vers\service-account.json
```

### 4. Google Cloud Vision (optionnel)

Si tu veux aussi utiliser Cloud Vision pour de l'OCR générique :

**Option A : Clé API simple** :
1. https://console.cloud.google.com/ → APIs & Services → Credentials
2. Create Credentials → API Key
3. Enable "Cloud Vision API"
4. Ajouter dans `.env` : `GOOGLE_CLOUD_API_KEY=votre_clé`

**Option B : Service Account JSON** :
- Réutiliser le même fichier JSON que Document AI

### 5. ChatGPT Vision (recommandé pour tableaux complexes) ⭐

**Configuration obligatoire** :

1. **Créer une clé API OpenAI** :
   - https://platform.openai.com/api-keys
   - Create new secret key
   - Copier la clé (commençant par sk-proj-... ou sk-...)

2. **Configurer le `.env`** :
```bash
OPENAI_API_KEY=sk-proj-votre_clé_ici
# Optionnel : personnaliser le calcul de coût
COST_PER_1M_INPUT=0.60
COST_PER_1M_OUTPUT=2.40
```

**Modèle utilisé** : `gpt-4o-mini` (vision)
**Coûts approximatifs** : ~0.60 USD / 1M tokens input, ~2.40 USD / 1M tokens output

### 6. Fichier .env

Le fichier `.env` peut contenir (selon les processors utilisés) :
```bash
# ChatGPT (recommandé)
OPENAI_API_KEY=sk-proj-votre_clé

# Document AI (alternatif)
GOOGLE_CLOUD_PROJECT_ID=your_project_id
DOCUMENT_AI_PROCESSOR_ID=your_processor_id
DOCUMENT_AI_LOCATION=eu
GOOGLE_APPLICATION_CREDENTIALS=C:\chemin\vers\service-account.json

# Google Cloud Vision (optionnel)
GOOGLE_CLOUD_API_KEY=votre_clé
```

**Note** : Le fichier `.env` est dans `.gitignore` et ne doit JAMAIS être commité.

---

## 📂 Structure des fichiers

```
ReadPicture/
├─ main.py                    # Point d'entrée
├─ requirements.txt           # Dépendances Python
├─ .env                       # Configuration (non versionné)
├─ .gitignore                 
├─ app/
│  ├─ __init__.py             # Charge le .env au démarrage
│  ├─ gui.py                  # Interface graphique
│  └─ processors/
│     ├─ __init__.py
│     ├─ base_processor.py
│     ├─ tesseract_processor.py
│     ├─ google_cloud_processor.py
│     ├─ document_ai_processor.py
│     ├─ chatgpt_processor.py
│     └─ export_processor.py
└─ doc/
   ├─ doc_main.md             # Cette doc
   └─ last_modif.md           # Journal des modifications
```

---

## 🔍 Ajout d'un nouveau processor

1. Créer `app/processors/mon_processor.py`
2. Hériter de `BaseProcessor`
3. Implémenter `process_image()` et `run()`
4. Ajouter dans `app/processors/__init__.py`
5. Ajouter un radio button dans `gui.py`
6. Ajouter la logique dans `_update_processor()`

**Exemple** :
```python
from .base_processor import BaseProcessor
from .export_processor import export_to_csv

class MonProcessor(BaseProcessor):
    def process_image(self, image_path: Path) -> List[str]:
        # Votre logique OCR ici
        return lines
    
    def run(self, image_path: Path, output_dir: Path | None = None) -> Path:
        lines = self.process_image(image_path)
        csv_path = output_dir / f"{image_path.stem}.csv"
        export_to_csv(lines, csv_path, debug=self.debug)
        return csv_path
```

---

## 🐛 Debug

**Mode debug activé par défaut** (`debug=True`) :

**Tesseract** génère dans `debug/` :
- Images prétraitées (original, gray, otsu, adaptive)
- Résultats de chaque config testée (txt)

**Export CSV** génère :
- `fichier.debug.txt` avec lignes brutes et structurées

**Logs** :
- Affichage console des résultats de chaque config
- Confiance moyenne pour chaque test

---

## 📝 TODO

- [x] Implémenter DocumentAIProcessor avec support Document AI
- [x] Implémenter ChatGPTProcessor avec support GPT-4o-mini Vision
- [ ] Tester Document AI vs ChatGPT sur vrais tableaux comptables
- [ ] Comparer les performances Tesseract vs Document AI vs ChatGPT
- [ ] Exploiter la détection native de tableaux de Document AI (actuellement on utilise juste le texte)
- [ ] Implémenter GoogleCloudProcessor une fois les credentials disponibles
- [ ] Ajouter un processor Azure Computer Vision ?
- [ ] Optimiser la détection de colonnes pour les tableaux complexes


