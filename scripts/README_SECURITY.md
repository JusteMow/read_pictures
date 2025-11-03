# 🔒 Scripts de Sécurité Git

Scripts pour éviter de commiter accidentellement des credentials/secrets.

---

## 📋 Scripts disponibles

### 1. `check_credentials.py` - Scanner de credentials

Scanne tous les fichiers du projet pour détecter :
- ✅ Google Cloud Project IDs
- ✅ Google Cloud API Keys
- ✅ Document AI Processor IDs
- ✅ OpenAI API Keys
- ✅ AWS Access Keys
- ✅ Azure Keys
- ✅ Private Keys (RSA/DSA)
- ✅ Secrets génériques (password, token, etc.)

**Usage manuel** :
```bash
# Scanner tout le projet
python scripts/check_credentials.py

# Scanner un dossier spécifique
python scripts/check_credentials.py --path app/

# Mode strict (signale même les exemples commentés)
python scripts/check_credentials.py --strict
```

**Sortie** :
- Exit code `0` : Aucun problème détecté
- Exit code `1` : Credentials suspects trouvés

---

### 2. `install_git_hook.py` - Installation du pre-commit hook

Installe automatiquement un hook Git qui **bloque les commits** si des credentials sont détectés.

**Installation** :
```bash
# À la racine du projet
python scripts/install_git_hook.py
```

**Fonctionnement** :
1. À chaque `git commit`, le scanner s'exécute automatiquement
2. Si un credential est détecté → **commit BLOQUÉ** ❌
3. Si rien n'est détecté → commit autorisé ✅

**Bypass** (DANGEREUX, seulement si faux positif) :
```bash
git commit --no-verify -m "Message"
```

---

## 🛠️ Configuration

### Ajouter des valeurs autorisées (whitelist)

Si le scanner signale des **faux positifs** (valeurs qui ne sont PAS des credentials réels), ajoutez-les dans `check_credentials.py` :

```python
WHITELIST = {
    "123456789012",          # Exemple générique
    "your_project_id",       # Placeholder
    "ma_valeur_exemple",     # Votre faux positif ici
}
```

### Ignorer des fichiers/dossiers

Par défaut, les dossiers `.venv`, `node_modules`, `.git`, etc. sont ignorés.

Pour ajouter d'autres exclusions :

```python
IGNORE_DIRS = {
    '.git', '__pycache__', 'venv',
    'mon_dossier_a_ignorer',  # Ajoutez ici
}

IGNORE_EXTENSIONS = {
    '.pyc', '.jpg', '.png',
    '.mon_extension',  # Ajoutez ici
}
```

---

## 🧪 Workflow recommandé

### Lors de la création d'un nouveau projet

1. **Initialiser Git** :
   ```bash
   git init
   ```

2. **Installer le hook de sécurité** :
   ```bash
   python scripts/install_git_hook.py
   ```

3. **Scanner avant le premier commit** :
   ```bash
   python scripts/check_credentials.py
   ```

4. **Commit si tout est OK** :
   ```bash
   git add .
   git commit -m "Initial commit"
   ```

---

### Avant chaque push public

```bash
# Scan manuel de sécurité
python scripts/check_credentials.py

# Si tout est OK
git push origin main
```

---

## 🚨 Que faire si un credential a été commité ?

### Si détecté AVANT le push

```bash
# Annuler le dernier commit (garde les modifications)
git reset --soft HEAD~1

# Nettoyer les credentials
# (éditer les fichiers pour remplacer par des placeholders)

# Re-commiter
git add .
git commit -m "Clean commit"
```

### Si déjà pushé sur GitHub

**Option 1 : Réécrire l'historique (repo récent/peu utilisé)**
```bash
# Filter-branch (remplacer les valeurs dans tout l'historique)
git filter-branch --force --tree-filter \
  "sed -i 's/VOTRE_VRAIE_VALEUR/placeholder/g' fichier.py || true" \
  --prune-empty -- --all

# Force push
git push -f origin main
```

**Option 2 : Supprimer le repo et recréer (plus sûr)**
1. Supprimer le repo GitHub
2. Régénérer les credentials côté provider (Google Cloud, AWS, etc.)
3. Recréer un repo propre

**Option 3 : GitHub Security Advisory**
- GitHub peut scanner et supprimer les secrets de l'historique
- Contact : https://github.com/security

---

## 📚 Patterns détectés

### Google Cloud Project ID
```
GOOGLE_CLOUD_PROJECT_ID=809671590699  ❌
GOOGLE_CLOUD_PROJECT_ID=your_project_id  ✅
```

### Google Cloud API Key
```
GOOGLE_CLOUD_API_KEY=AIzaSyD...  ❌
GOOGLE_CLOUD_API_KEY=your_api_key  ✅
```

### Document AI Processor ID
```
DOCUMENT_AI_PROCESSOR_ID=e3ef773999ff0981  ❌
DOCUMENT_AI_PROCESSOR_ID=your_processor_id  ✅
```

### Private Keys
```
-----BEGIN RSA PRIVATE KEY-----  ❌
(Toujours dans fichiers gitignorés)
```

---

## 🎯 Bonnes pratiques

### ✅ À FAIRE
- Utiliser `.env` pour les credentials (dans `.gitignore`)
- Créer `.env.example` avec des placeholders génériques
- Installer le pre-commit hook sur tous les projets
- Scanner manuellement avant chaque push public
- Utiliser des Service Accounts pour les API cloud
- Régénérer les credentials si fuite suspectée

### ❌ À ÉVITER
- Hardcoder des credentials dans le code source
- Commiter des fichiers `.env` ou `.json` de credentials
- Mettre des vraies valeurs dans la documentation
- Bypass le hook sans vérifier manuellement
- Laisser des credentials dans les messages de commit

---

## 🔗 Ressources

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [OWASP Secrets Management](https://owasp.org/www-community/Secrets_Management)

---

## 📝 Maintenance

### Mettre à jour les patterns

Si de nouveaux types de credentials doivent être détectés, éditez `check_credentials.py` :

```python
CREDENTIAL_PATTERNS = {
    "Mon Nouveau Provider": [
        r'pattern_regex_ici',
    ],
    # ... autres patterns
}
```

### Tester les patterns

```python
# Dans check_credentials.py, ajoutez des tests
test_string = "GOOGLE_CLOUD_PROJECT_ID=809671590699"
for pattern in CREDENTIAL_PATTERNS["Google Cloud Project ID"]:
    if re.search(pattern, test_string):
        print(f"✅ Pattern détecté : {pattern}")
```

---

**Version** : 1.0  
**Dernière mise à jour** : Novembre 2025

