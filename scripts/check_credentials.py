"""
Script de vérification de sécurité avant commit Git
Scanne tous les fichiers pour détecter des credentials/secrets potentiels

Usage:
    python scripts/check_credentials.py [--path chemin] [--strict]
"""

import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import fnmatch
import subprocess

# Fix encodage Windows pour les emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Patterns de détection de credentials
CREDENTIAL_PATTERNS = {
    "Google Cloud Project ID": [
        r'\d{12}',  # 12 chiffres consécutifs
        r'GOOGLE_CLOUD_PROJECT_ID\s*[=:]\s*["\']?\d{12}["\']?',
    ],
    "Google Cloud API Key": [
        r'AIza[0-9A-Za-z\-_]{35}',
        r'GOOGLE_(?:CLOUD_)?API_KEY\s*[=:]\s*["\']?AIza[0-9A-Za-z\-_]{35}["\']?',
    ],
    "Document AI Processor ID": [
        r'[a-f0-9]{16}',  # 16 caractères hexa
        r'DOCUMENT_AI_PROCESSOR_ID\s*[=:]\s*["\']?[a-f0-9]{16}["\']?',
    ],
    "OpenAI API Key": [
        r'sk-[a-zA-Z0-9]{48}',
        r'OPENAI_API_KEY\s*[=:]\s*["\']?sk-[a-zA-Z0-9]{48}["\']?',
    ],
    "AWS Access Key": [
        r'AKIA[0-9A-Z]{16}',
        r'AWS_ACCESS_KEY_ID\s*[=:]\s*["\']?AKIA[0-9A-Z]{16}["\']?',
    ],
    "Azure Key": [
        r'[a-zA-Z0-9]{32,}',
        r'AZURE_(?:CLIENT_)?(?:SECRET|KEY)\s*[=:]\s*["\']?[a-zA-Z0-9]{32,}["\']?',
    ],
    "Private Key": [
        r'-----BEGIN (?:RSA |DSA )?PRIVATE KEY-----',
    ],
    "Generic Secret": [
        r'(?:password|passwd|pwd|secret|token)\s*[=:]\s*["\'][^"\']{8,}["\']',
    ],
}

# Extensions à ignorer
IGNORE_EXTENSIONS = {
    '.pyc', '.pyo', '.exe', '.dll', '.so', '.dylib',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
    '.mp3', '.mp4', '.avi', '.mov', '.wav',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
}

# Dossiers à ignorer
IGNORE_DIRS = {
    '.git', '__pycache__', 'node_modules', '.venv', 'venv',
    'dist', 'build', '.egg-info', '.pytest_cache', '.mypy_cache',
}

# Fichiers à ignorer (contiennent légitimement des patterns de credentials)
IGNORE_FILES = {
    'check_credentials.py',
    'README_SECURITY.md',
}

# Whitelist : valeurs autorisées (exemples dans la doc)
WHITELIST = {
    "123456789012",  # Exemple générique project ID
    "your_project_id",
    "your_processor_id",
    "your_api_key",
    "your_secret_here",
    "example_value",
    "dummy_value",
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",  # Alphabet complet (valid_chars)
}


class CredentialScanner:
    def __init__(self, root_path: Path, strict: bool = False):
        self.root_path = root_path
        self.strict = strict
        self.issues: List[Dict] = []
        self.has_git = self._check_git_available()

    def _check_git_available(self) -> bool:
        """Vérifie si Git est disponible"""
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            # Vérifier si on est dans un repo Git
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def _is_git_ignored(self, path: Path) -> bool:
        """Utilise 'git check-ignore' pour vérifier si un fichier est ignoré"""
        if not self.has_git:
            return False
        
        try:
            result = subprocess.run(
                ['git', 'check-ignore', str(path)],
                cwd=self.root_path,
                capture_output=True,
                text=True
            )
            # Exit code 0 = fichier ignoré, 1 = non ignoré
            return result.returncode == 0
        except Exception:
            return False

    def should_ignore(self, path: Path) -> bool:
        """Vérifie si un fichier/dossier doit être ignoré"""
        # Vérifier .gitignore via Git natif (le plus fiable)
        if self._is_git_ignored(path):
            return True
        
        # Fichiers spécifiques
        if path.name in IGNORE_FILES:
            return True
        
        # Extensions
        if path.suffix.lower() in IGNORE_EXTENSIONS:
            return True
        
        # Dossiers parents
        for parent in path.parents:
            if parent.name in IGNORE_DIRS:
                return True
        
        return False

    def is_whitelisted(self, value: str) -> bool:
        """Vérifie si une valeur est dans la whitelist"""
        value_clean = value.strip('\'"')
        return value_clean in WHITELIST

    def scan_file(self, file_path: Path):
        """Scanne un fichier pour détecter des credentials"""
        if self.should_ignore(file_path):
            return

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"⚠️  Impossible de lire {file_path}: {e}")
            return

        for credential_type, patterns in CREDENTIAL_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    matched_value = match.group(0)
                    
                    # Skip si whitelisted
                    if self.is_whitelisted(matched_value):
                        continue
                    
                    # Trouver le numéro de ligne
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = content.split('\n')[line_num - 1].strip()
                    
                    # En mode strict, tout est suspect
                    # En mode normal, on filtre les faux positifs évidents
                    if not self.strict:
                        # Skip si c'est un commentaire d'exemple
                        if line_content.startswith('#') and any(word in line_content.lower() for word in ['example', 'exemple', 'ex:', 'dummy']):
                            continue
                    
                    self.issues.append({
                        'file': str(file_path.relative_to(self.root_path)),
                        'line': line_num,
                        'type': credential_type,
                        'matched': matched_value,
                        'context': line_content[:100],  # Max 100 chars
                    })

    def scan_directory(self):
        """Scanne récursivement tout le projet"""
        for root, dirs, files in os.walk(self.root_path):
            # Filtrer les dossiers à ignorer
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                self.scan_file(file_path)

    def report(self) -> bool:
        """Affiche le rapport et retourne True si des problèmes ont été trouvés"""
        if not self.issues:
            print("✅ Aucun credential suspect détecté.")
            return False

        print(f"\n🚨 {len(self.issues)} credential(s) suspect(s) détecté(s) !\n")
        
        # Grouper par fichier
        files_with_issues = {}
        for issue in self.issues:
            file = issue['file']
            if file not in files_with_issues:
                files_with_issues[file] = []
            files_with_issues[file].append(issue)
        
        for file, issues in files_with_issues.items():
            print(f"📄 {file}")
            for issue in issues:
                print(f"   Ligne {issue['line']:4d} | {issue['type']}")
                print(f"              | Valeur: {issue['matched']}")
                print(f"              | {issue['context']}")
                print()
        
        print("⚠️  ATTENTION : Ne commitez PAS si ces valeurs sont réelles !")
        print("💡 Si ce sont des exemples/placeholders, ajoutez-les à WHITELIST dans le script.\n")
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Scanner de credentials pour Git")
    parser.add_argument('--path', type=str, default='.', help="Chemin à scanner (défaut: répertoire courant)")
    parser.add_argument('--strict', action='store_true', help="Mode strict : signale même les exemples commentés")
    
    args = parser.parse_args()
    
    root_path = Path(args.path).resolve()
    
    if not root_path.exists():
        print(f"❌ Erreur : Le chemin {root_path} n'existe pas.")
        sys.exit(1)
    
    print(f"🔍 Scan de sécurité : {root_path}")
    print(f"   Mode: {'STRICT' if args.strict else 'NORMAL'}\n")
    
    scanner = CredentialScanner(root_path, strict=args.strict)
    scanner.scan_directory()
    
    has_issues = scanner.report()
    
    if has_issues:
        sys.exit(1)  # Exit code 1 pour bloquer le commit si utilisé en pre-commit
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

