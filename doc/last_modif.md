## 2025-11-03 - Amélioration fichiers debug avec métadonnées processor

Modification : export_processor.py - ajout paramètre metadata pour export_to_csv() et export_structured_to_csv()
Modification : Tous les processors (ChatGPT, Document AI, Tesseract, Google Cloud Vision) passent leurs métadonnées à l'export
Amélioration : Fichiers .debug.txt affichent maintenant le processor utilisé, modèle, tokens consommés et coût estimé (ChatGPT)

---

## 2025-11-03 - Ajout ChatGPT Vision processor

Implémentation : chatgpt_processor.py pour ChatGPT Vision (GPT-4o-mini, performant pour tableaux complexes)
Modification : gui.py avec 4ème radio button "ChatGPT Vision (API, performant)"
Configuration : Ajout variable d'environnement OPENAI_API_KEY + optionnel COST_PER_1M_INPUT/OUTPUT
Configuration : Mise à jour requirements.txt (openai>=1.0)
Doc : Mise à jour doc_main.md avec section ChatGPTProcessor détaillée

---

## 2025-11-02 - Ajout Document AI processor

Implémentation : document_ai_processor.py pour Google Document AI (spécialisé tableaux et documents structurés)
Modification : gui.py avec 3ème radio button "Document AI (API, tableaux)"
Configuration : Ajout variables d'environnement Document AI (DOCUMENT_AI_PROCESSOR_ID, DOCUMENT_AI_LOCATION, GOOGLE_CLOUD_PROJECT_ID)
Configuration : Mise à jour requirements.txt (google-cloud-documentai)
Configuration : Fichiers .env et .env.example avec config complète du processor Document AI

---

## 2025-11-02 - Refactorisation architecture processors modulaire

Implémentation : Création dossier `app/processors/` avec architecture modulaire
Implémentation : base_processor.py (classe abstraite), tesseract_processor.py, google_cloud_processor.py, export_processor.py
Modification : gui.py avec radio buttons pour sélectionner le processor (Tesseract / Google Cloud Vision)
Configuration : Ajout .env pour credentials Google Cloud, mise à jour requirements.txt (python-dotenv, google-cloud-vision)
Suppression : app/processor.py (migré dans processors/)
Doc : Création doc_main.md avec documentation complète de l'architecture

---

## Implémentation initiale Application OCR

Styles : ajout requirements.txt
Implémentation : app/__init__.py créé
Implémentation : app/processor.py (class OCRProcessor)
Implémentation : app/gui.py (class App)
Implémentation : main.py point d'entrée

Implémentation : Création de la structure de base du projet (main.py, app/gui.py, app/processor.py), ajout de requirements.txt.

Debug : Ajout vérification installation Tesseract au démarrage 

Amélioration : OCRProcessor avec prétraitement avancé (redimensionnement, CLAHE, débruitage, test multiple configs Tesseract), debug mode activé par défaut 

Amélioration : Export CSV avec détection automatique des colonnes (espaces multiples, tabulations, patterns texte/nombre), ajout fichier debug pour analyse structuration 
