# 2. Ajoute le submodule (choisis le dossier de destination)
git submodule add https://github.com/JusteMow/tk_shared.git _shared/tkshared

# 3. Installe le package en mode éditable
pip install -e _shared/tkshared

# 4. Commit le submodule
git add .gitmodules _shared/tkshared
git commit -m "Add tkshared submodule"