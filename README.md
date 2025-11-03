# ReadPicture - OCR de tableaux

Application OCR pour la transcription automatique de tableaux et documents en fichiers CSV.

## 🚀 Installation

### 1. Cloner le projet

```bash
git clone <repo_url>
cd ReadPicture
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

**Packages installés** :
- `opencv-python` : Traitement d'image
- `pytesseract` : Interface Python pour Tesseract OCR
- `pillow` : Manipulation d'images
- `pandas` : Export CSV structuré
- `python-dotenv` : Gestion des variables d'environnement
- `google-cloud-vision` : API Google Cloud Vision

### 3. Installer Tesseract OCR

**Tesseract est obligatoire** pour le processor local.

**Windows** :
1. Télécharger : https://github.com/UB-Mannheim/tesseract/wiki
2. Installer en cochant **"Add to PATH"**
3. Redémarrer l'application après installation

**Linux/Mac** :
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-fra

# Mac
brew install tesseract tesseract-lang
```

### 4. Configuration Google Document AI (recommandé pour tableaux)

Pour utiliser **Document AI** et obtenir la meilleure précision sur les tableaux :

#### Étape 1 : Créer un processor Document AI

1. Aller sur https://console.cloud.google.com/ai/document-ai
2. **Create Processor** → Sélectionner **"Document OCR"**
3. Donner un nom (ex: OCR1) et choisir la région (ex: eu)
4. Noter l'**ID du processor** et la **région**

#### Étape 2 : Créer un Service Account (obligatoire)

1. https://console.cloud.google.com/iam-admin/serviceaccounts
2. **Create Service Account**
3. Donner les permissions **Document AI User**
4. **Actions** → **Manage Keys** → **Add Key** → **Create new key** → **JSON**
5. Télécharger le fichier JSON

#### Étape 3 : Configurer le .env

Créer un fichier `.env` à la racine du projet :

```bash
# .env
GOOGLE_CLOUD_PROJECT_ID=your_project_id
DOCUMENT_AI_PROCESSOR_ID=your_processor_id
DOCUMENT_AI_LOCATION=eu
GOOGLE_APPLICATION_CREDENTIALS=C:\chemin\vers\service-account.json
```

**Note** : Le fichier `.env` est déjà dans `.gitignore` et ne sera jamais commité.

### 5. Configuration Google Cloud Vision (optionnel)

Si tu veux aussi utiliser Cloud Vision API :

- **Clé API simple** : Ajouter `GOOGLE_CLOUD_API_KEY=votre_clé` dans `.env`
- **Service Account** : Réutiliser le même JSON que Document AI

---

## 🎮 Utilisation

### Lancer l'application

```bash
python main.py
```

### Interface graphique

1. **Sélectionner le moteur OCR** :
   - ○ Tesseract (local, gratuit)
   - ○ Google Cloud Vision (API, plus précis)

2. **Choisir image(s)** : Sélectionne les fichiers à traiter (PNG, JPG, JPEG, BMP)

3. **Transcrire** : Lance le traitement

4. **Résultats** :
   - Fichiers CSV générés dans `output/`
   - Logs affichés dans l'interface

### Fichiers générés

```
image.png
  └─ output/
      └─ image.csv          # Données structurées en colonnes
  └─ debug/ (si mode debug actif)
      ├─ image_original.png
      ├─ image_gray.png
      ├─ image_otsu.png
      ├─ image_adaptive.png
      ├─ image_result_*.txt
      └─ image.debug.txt    # Analyse détaillée
```

---

## 🏗️ Architecture

```
ReadPicture/
├─ main.py                    # Point d'entrée
├─ requirements.txt
├─ .env                       # Configuration (non versionné)
├─ app/
│  ├─ __init__.py             # Charge .env au démarrage
│  ├─ gui.py                  # Interface Tkinter
│  └─ processors/
│     ├─ base_processor.py          # Classe abstraite
│     ├─ tesseract_processor.py     # OCR Tesseract
│     ├─ google_cloud_processor.py  # OCR Google Cloud Vision
│     ├─ document_ai_processor.py   # OCR Document AI (tableaux)
│     └─ export_processor.py        # Export CSV commun
└─ doc/
   ├─ doc_main.md             # Documentation complète
   └─ last_modif.md           # Journal des modifications
```

### Processors disponibles

#### 🔹 TesseractProcessor (par défaut)

- OCR local gratuit
- Prétraitement avancé (redimensionnement, CLAHE, débruitage)
- Test automatique de 10 configurations (5 PSM × 2 seuils)
- Sélection du meilleur résultat (confiance maximale)

#### 🔹 GoogleCloudProcessor

- OCR via API Google Cloud Vision
- Bonne précision pour OCR générique
- Détection automatique de langue
- Gestion des rotations et perspectives
- **Pricing** : Gratuit jusqu'à 1000 requêtes/mois

#### 🔹 DocumentAIProcessor (⭐ RECOMMANDÉ POUR TABLEAUX)

- OCR via API Google Document AI
- **Spécialisé** dans les documents structurés (tableaux, formulaires, factures)
- Meilleure compréhension de la mise en page
- Détection native des tableaux
- Extraction de champs structurés
- **Pricing** : Gratuit jusqu'à 1000 pages/mois

---

## 📝 Fonctionnalités

- ✅ OCR multilingue (français par défaut pour Tesseract)
- ✅ Détection automatique des colonnes
- ✅ Export CSV structuré avec nommage automatique
- ✅ Traitement par batch (plusieurs images)
- ✅ Mode debug avec fichiers intermédiaires
- ✅ Gestion d'erreurs robuste
- ✅ Fallback automatique Tesseract si Google Cloud échoue

---

## 🐛 Troubleshooting

### Erreur "Tesseract n'est pas installé"

➡️ Installer Tesseract OCR et l'ajouter au PATH (voir section 3)

### Erreur "Credentials Google Cloud manquants" ou "Configuration Document AI incomplète"

➡️ L'app bascule automatiquement sur Tesseract. Pour utiliser Document AI ou Google Cloud Vision, créer le fichier `.env` (voir sections 4 et 5)

### Erreur "Package google-cloud-documentai non installé"

➡️ Installer avec : `pip install google-cloud-documentai`

### Images mal reconnues

➡️ Activer le mode debug (déjà actif par défaut) et consulter les fichiers dans `debug/` pour analyser le prétraitement

### Colonnes mal détectées

➡️ La fonction `detect_columns()` utilise plusieurs heuristiques. Si le tableau est trop complexe, envisager un prétraitement manuel de l'image ou ajuster les seuils dans `export_processor.py`

---

## 🔧 Développement

### Ajouter un nouveau processor

1. Créer `app/processors/mon_processor.py`
2. Hériter de `BaseProcessor`
3. Implémenter `process_image()` et `run()`
4. Ajouter dans `app/processors/__init__.py`
5. Ajouter un radio button dans `gui.py`

Exemple :

```python
from .base_processor import BaseProcessor
from .export_processor import export_to_csv

class MonProcessor(BaseProcessor):
    def process_image(self, image_path: Path) -> List[str]:
        # Votre logique OCR
        return lines
    
    def run(self, image_path: Path, output_dir: Path | None = None) -> Path:
        lines = self.process_image(image_path)
        csv_path = output_dir / f"{image_path.stem}.csv"
        export_to_csv(lines, csv_path, debug=self.debug)
        return csv_path
```

---

## 📚 Documentation

Voir `doc/doc_main.md` pour la documentation complète de l'architecture.

---

## 📜 Licence

(À définir)

---

## 🙏 Remerciements

- **Tesseract OCR** : https://github.com/tesseract-ocr/tesseract
- **Google Cloud Vision API** : https://cloud.google.com/vision


