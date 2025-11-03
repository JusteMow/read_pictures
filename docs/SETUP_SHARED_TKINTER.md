# Setup complet : Modules Tkinter partagés

## Architecture proposée

```
C:\Users\MO\Documents\Tools\
├── TkinterSharedUI/              # Repo Git séparé
│   ├── .git/
│   ├── tkshared/
│   │   ├── __init__.py
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── custom_button.py
│   │   │   ├── custom_grid.py
│   │   │   └── custom_scrollbar.py
│   │   ├── dialogs/
│   │   │   ├── __init__.py
│   │   │   └── modal_base.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── theme.py
│   ├── setup.py
│   ├── README.md
│   └── requirements.txt
│
├── ReadPicture/
│   ├── .git/
│   ├── shared_ui/               # Git submodule → TkinterSharedUI
│   ├── src/
│   └── requirements.txt
│
└── AutreProjet/
    ├── .git/
    ├── shared_ui/               # Git submodule → TkinterSharedUI
    └── requirements.txt
```

---

## Étape 1 : Créer le repo TkinterSharedUI

### 1.1 Structure de base

```bash
mkdir C:\Users\MO\Documents\Tools\TkinterSharedUI
cd C:\Users\MO\Documents\Tools\TkinterSharedUI
git init
```

### 1.2 Créer setup.py

```python
from setuptools import setup, find_packages

setup(
    name="tkshared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Dépendances tkinter si nécessaire
        "Pillow",  # Exemple
    ],
    python_requires=">=3.8",
)
```

### 1.3 Créer tkshared/__init__.py

```python
"""
Modules Tkinter partagés entre projets
"""
__version__ = "0.1.0"

from .widgets import *
from .dialogs import *
```

### 1.4 Exemple de widget : tkshared/widgets/custom_button.py

```python
import tkinter as tk
from tkinter import ttk

class CustomButton(ttk.Button):
    """
    Bouton personnalisé avec style uniforme
    """
    def __init__(self, parent, **kwargs):
        # Style par défaut
        style_defaults = {
            'padding': (10, 5),
        }
        style_defaults.update(kwargs)
        super().__init__(parent, **style_defaults)
```

### 1.5 Push sur GitHub

```bash
# Sur GitHub : créer le repo "TkinterSharedUI" (public ou privé)
git add .
git commit -m "Initial commit: shared tkinter modules"
git remote add origin https://github.com/TON_USERNAME/TkinterSharedUI.git
git push -u origin main
```

---

## Étape 2 : Ajouter le submodule dans ReadPicture

```bash
cd C:\Users\MO\Documents\Tools\ReadPicture

# Ajouter le submodule
git submodule add https://github.com/TON_USERNAME/TkinterSharedUI.git shared_ui

# Installer le package en mode éditable
pip install -e shared_ui

# Commit
git add .gitmodules shared_ui
git commit -m "Add shared UI submodule"
git push
```

---

## Étape 3 : Utiliser dans le code

### Dans ReadPicture/src/main.py

```python
# Import depuis le package partagé
from tkshared.widgets import CustomButton
from tkshared.dialogs import ModalBase
from tkshared.utils import apply_theme

# Utilisation normale
button = CustomButton(parent, text="Click me")
```

---

## Workflow de développement

### Modifier le module partagé

```bash
cd C:\Users\MO\Documents\Tools\ReadPicture\shared_ui

# Éditer les fichiers
# Les changements sont immédiatement visibles (mode -e)

# Commit et push les changements
git add .
git commit -m "Add new widget XYZ"
git push origin main
```

### Récupérer les mises à jour dans un autre projet

```bash
cd C:\Users\MO\Documents\Tools\AutreProjet

# Mettre à jour le submodule
git submodule update --remote shared_ui

# Commit la nouvelle référence
git add shared_ui
git commit -m "Update shared UI to latest version"
```

### Cloner un projet avec submodules

```bash
# Option 1 : Clone avec submodules
git clone --recurse-submodules https://github.com/TON_USERNAME/ReadPicture.git

# Option 2 : Clone normal puis init submodules
git clone https://github.com/TON_USERNAME/ReadPicture.git
cd ReadPicture
git submodule init
git submodule update

# Installer le package
pip install -e shared_ui
```

---

## Commandes Git utiles pour submodules

```bash
# Voir l'état des submodules
git submodule status

# Mettre à jour tous les submodules
git submodule update --remote --merge

# Exécuter une commande dans tous les submodules
git submodule foreach 'git pull origin main'

# Supprimer un submodule
git submodule deinit shared_ui
git rm shared_ui
rm -rf .git/modules/shared_ui
```

---

## Alternative : Package local sans Git submodule

Si tu veux quelque chose de plus simple (sans submodule) :

### Structure
```
C:\Users\MO\Documents\Tools\
├── tkshared/                    # Package local simple
│   ├── tkshared/
│   │   └── ...
│   └── setup.py
├── ReadPicture/
│   └── requirements.txt         # -e ../tkshared
└── AutreProjet/
    └── requirements.txt         # -e ../tkshared
```

### requirements.txt dans chaque projet
```
-e ../tkshared
```

**Avantage** : Plus simple, pas de Git à gérer
**Inconvénient** : Pas de versioning, difficile à partager entre machines

---

## Recommandation

Pour ton cas : **Git submodule** est le meilleur choix car :
- ✅ Tu push/pull déjà tes projets sur GitHub
- ✅ Versioning automatique
- ✅ Facile à synchroniser entre machines
- ✅ Chaque projet peut utiliser une version spécifique si nécessaire
- ✅ Standard de l'industrie

Le workflow devient :
1. Modifier dans `shared_ui/` du projet actif
2. Push les changements du submodule
3. Update dans les autres projets quand tu veux

