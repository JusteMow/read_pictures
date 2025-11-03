"""
Installer le pre-commit hook Git pour vérifier les credentials

Usage:
    python scripts/install_git_hook.py
"""

from pathlib import Path
import shutil
import sys

HOOK_CONTENT = """#!/usr/bin/env python3
\"\"\"
Pre-commit hook Git - Vérifie les credentials avant chaque commit
Installé automatiquement par scripts/install_git_hook.py
\"\"\"

import sys
import subprocess
from pathlib import Path

# Chemin vers le script de vérification
script_path = Path(__file__).parent.parent.parent / "scripts" / "check_credentials.py"

if not script_path.exists():
    print("⚠️  Script check_credentials.py introuvable, hook désactivé.")
    sys.exit(0)

print("🔍 Vérification des credentials avant commit...")

try:
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if result.returncode != 0:
        print("\\n❌ COMMIT BLOQUÉ : Credentials suspects détectés !")
        print("💡 Vérifiez les fichiers ci-dessus ou ajoutez les valeurs à WHITELIST.")
        print("\\n🚨 Pour bypass (DANGEREUX) : git commit --no-verify\\n")
        sys.exit(1)
    
    print("✅ Aucun credential suspect, commit autorisé.\\n")
    sys.exit(0)

except Exception as e:
    print(f"⚠️  Erreur lors de la vérification : {e}")
    print("   Le commit sera autorisé mais vérifiez manuellement !\\n")
    sys.exit(0)
"""


def install_hook():
    """Installe le pre-commit hook dans .git/hooks/"""
    
    # Vérifier qu'on est dans un repo Git
    git_dir = Path(".git")
    if not git_dir.exists():
        print("❌ Erreur : Pas de dossier .git trouvé.")
        print("   Assurez-vous d'être à la racine du projet Git.")
        sys.exit(1)
    
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    
    hook_path = hooks_dir / "pre-commit"
    
    # Backup si un hook existe déjà
    if hook_path.exists():
        backup_path = hooks_dir / "pre-commit.backup"
        print(f"⚠️  Un pre-commit hook existe déjà.")
        print(f"   Sauvegarde dans : {backup_path}")
        shutil.copy(hook_path, backup_path)
    
    # Écrire le nouveau hook
    hook_path.write_text(HOOK_CONTENT, encoding='utf-8')
    
    # Rendre exécutable (Unix/Mac)
    try:
        hook_path.chmod(0o755)
    except Exception:
        pass  # Ignore sur Windows
    
    print(f"✅ Pre-commit hook installé : {hook_path}")
    print("\n📋 Fonctionnement :")
    print("   • À chaque 'git commit', les fichiers seront scannés automatiquement")
    print("   • Si un credential est détecté, le commit sera BLOQUÉ")
    print("   • Pour bypass (dangereux) : git commit --no-verify")
    print("\n🧪 Pour tester maintenant :")
    print("   python scripts/check_credentials.py")


if __name__ == "__main__":
    install_hook()

