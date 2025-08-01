# Guide de Construction d'Exécutable (.exe)
## Système de Gestion des Chèques

### Option 1: Construction avec PyInstaller (Recommandée)

#### Étapes pour construire l'exécutable sur Windows:

1. **Préparez l'environnement Windows:**
   ```bash
   # Téléchargez le projet depuis Replit
   # Installez Python 3.11+ sur Windows
   # Ouvrez l'invite de commandes (cmd) dans le dossier du projet
   ```

2. **Installez les dépendances:**
   ```bash
   pip install -r requirements_exe.txt
   ```

3. **Exécutez le script de construction:**
   ```bash
   python build_exe.py
   ```

#### Construction manuelle avec PyInstaller:

```bash
# Commande de base
pyinstaller --onefile --name=GestionCheques ^
  --add-data="templates;templates" ^
  --add-data="static;static" ^
  --add-data="utils;utils" ^
  --add-data="routes;routes" ^
  --hidden-import=flask ^
  --hidden-import=flask_sqlalchemy ^
  --hidden-import=flask_login ^
  --hidden-import=flask_wtf ^
  --hidden-import=wtforms ^
  --hidden-import=sqlalchemy ^
  --hidden-import=werkzeug ^
  --hidden-import=models ^
  --hidden-import=forms ^
  --hidden-import=app ^
  --hidden-import=openpyxl ^
  --hidden-import=reportlab ^
  --hidden-import=apscheduler ^
  desktop_main.py
```

### Option 2: Utilisation d'auto-py-to-exe (Interface Graphique)

1. **Installez auto-py-to-exe:**
   ```bash
   pip install auto-py-to-exe
   ```

2. **Lancez l'interface graphique:**
   ```bash
   auto-py-to-exe
   ```

3. **Configuration dans l'interface:**
   - **Script Location:** `desktop_main.py`
   - **Onefile:** One File
   - **Console Window:** Console Based
   - **Additional Files:**
     - `templates` → `templates`
     - `static` → `static`
     - `utils` → `utils`
     - `routes` → `routes`
   - **Hidden Imports:** `flask,flask_sqlalchemy,flask_login,models,forms,app`

### Option 3: Construction avec cx_Freeze

1. **Installez cx_Freeze:**
   ```bash
   pip install cx_Freeze
   ```

2. **Créez setup.py:**
   ```python
   from cx_Freeze import setup, Executable
   
   build_exe_options = {
       "packages": ["flask", "sqlalchemy", "wtforms", "openpyxl"],
       "include_files": ["templates", "static", "utils", "routes"]
   }
   
   setup(
       name="GestionCheques",
       version="1.0",
       description="Système de Gestion des Chèques",
       options={"build_exe": build_exe_options},
       executables=[Executable("desktop_main.py")]
   )
   ```

3. **Construisez l'exécutable:**
   ```bash
   python setup.py build
   ```

### Fichiers Nécessaires pour l'Exécutable

#### desktop_main.py (Point d'entrée principal)
```python
#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Configuration pour l'exécutable standalone
if getattr(sys, 'frozen', False):
    app_dir = Path(sys.executable).parent
    os.environ['FLASK_ENV'] = 'production'
else:
    app_dir = Path(__file__).parent
    os.environ['FLASK_ENV'] = 'development'

# Création des dossiers de données
data_dir = app_dir / 'data'
data_dir.mkdir(exist_ok=True)
(data_dir / 'excel').mkdir(exist_ok=True)
(data_dir / 'exports').mkdir(exist_ok=True)
(data_dir / 'uploads').mkdir(exist_ok=True)

# Variables d'environnement
os.environ['DATABASE_URL'] = f'sqlite:///{data_dir}/cheques.db'
os.environ['SESSION_SECRET'] = 'KSr8293NEv711HU16ZIr14Hxp13hv_ghVJVJgAgxkwo'
os.environ['UPLOAD_FOLDER'] = str(data_dir / 'uploads')
os.environ['EXCEL_FOLDER'] = str(data_dir / 'excel')
os.environ['EXPORTS_FOLDER'] = str(data_dir / 'exports')
os.environ['DATA_FOLDER'] = str(data_dir)

def main():
    try:
        from app import create_app
        app = create_app()
        
        print("=" * 60)
        print("   SYSTÈME DE GESTION DES CHÈQUES")
        print("=" * 60)
        print(f"Application démarrée depuis: {app_dir}")
        print("🌐 Accédez à: http://localhost:5000")
        print("👤 Connexion: manal / manalcedesa")
        print("=" * 60)
        print("Appuyez sur Ctrl+C pour arrêter")
        print("=" * 60)
        
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\nApplication arrêtée.")
        sys.exit(0)
    except Exception as e:
        print(f"Erreur: {e}")
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### Instructions d'Utilisation de l'Exécutable

1. **Lancement:**
   - Double-cliquez sur `GestionCheques.exe`
   - L'application démarre automatiquement

2. **Accès:**
   - Ouvrez votre navigateur web
   - Allez à `http://localhost:5000`
   - Connectez-vous avec: `manal` / `manalcedesa`

3. **Données:**
   - Base de données SQLite créée automatiquement
   - Dossier `data` créé à côté de l'exécutable
   - Fichiers Excel exportés dans `data/excel`

### Résolution de Problèmes

#### Erreur "Module non trouvé":
- Ajoutez le module manquant dans `--hidden-import`
- Vérifiez que toutes les dépendances sont installées

#### Erreur de taille de fichier:
- L'exécutable peut faire 50-100 MB (normal pour Flask)
- Utilisez `--exclude-module` pour supprimer les modules inutiles

#### Erreur de base de données:
- Vérifiez les permissions d'écriture
- Assurez-vous que le dossier `data` peut être créé

#### Erreur de port 5000 occupé:
- Fermez les autres applications utilisant le port 5000
- Modifiez le port dans `desktop_main.py` si nécessaire

### Notes Importantes

1. **Sécurité:**
   - L'exécutable utilise SQLite (pas PostgreSQL)
   - Parfait pour un usage desktop/offline
   - Données stockées localement

2. **Performance:**
   - Premier démarrage peut être lent (initialisation)
   - Performances normales après le démarrage

3. **Distribution:**
   - L'exécutable est portable
   - Peut être copié sur d'autres ordinateurs Windows
   - Aucune installation Python requise sur la machine cible

### Commandes Rapides

```bash
# Construction rapide (Windows)
pip install pyinstaller
pyinstaller --onefile --name=GestionCheques desktop_main.py

# Avec interface graphique
pip install auto-py-to-exe
auto-py-to-exe

# Test de l'exécutable
./dist/GestionCheques.exe
```

Cette approche garantit un exécutable Windows fonctionnel pour votre système de gestion des chèques.