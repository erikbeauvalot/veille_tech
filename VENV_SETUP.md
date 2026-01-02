# Configuration de l'Environnement Virtuel

## ✅ État actuel

L'environnement virtuel Python a été créé et configuré avec succès.

- **Localisation** : `venv/`
- **Python version** : 3.9
- **Dépendances installées** : 24 packages
- **Dépendances clés** :
  - `feedparser` - Analyse des flux RSS
  - `requests` - Requêtes HTTP
  - `python-dotenv` - Gestion des variables d'environnement
  - `anthropic` - API Claude pour traduction

## 🚀 Utilisation quotidienne

### Méthode recommandée (Utiliser les scripts)

#### macOS / Linux
```bash
./run.sh                    # Lancer l'application
./run.sh --dry-run         # Tester sans envoyer d'email
./run.sh --force           # Forcer la récupération de tous les articles
```

#### Windows
```cmd
run.bat                     # Lancer l'application
run.bat --dry-run          # Tester sans envoyer d'email
run.bat --force            # Forcer la récupération de tous les articles
```

### Méthode manuelle (Activation explicite)

#### macOS / Linux
```bash
source venv/bin/activate
python main.py [options]
deactivate
```

#### Windows
```cmd
venv\Scripts\activate.bat
python main.py [options]
deactivate
```

## 📦 Gérer les dépendances

### Afficher les paquets installés
```bash
source venv/bin/activate
pip list
```

### Ajouter un nouveau paquet
```bash
source venv/bin/activate
pip install nom_du_paquet
pip freeze > requirements.txt  # Mettre à jour requirements.txt
```

### Réinstaller tous les paquets
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Mettre à jour pip (macOS/Linux)
```bash
source venv/bin/activate
pip install --upgrade pip
```

## 📋 Points importants

⚠️ **IMPORTANT** :
- Ne JAMAIS exécuter `python main.py` directement en dehors du venv
- Toujours utiliser `./run.sh` ou activer le venv avant d'exécuter le code
- Ne pas inclure le dossier `venv/` dans le contrôle de version (il y a un `.gitignore`)

## 🔧 Dépannage

### Le script run.sh ne s'exécute pas
```bash
chmod +x run.sh
```

### Erreur "command not found: python"
Assurez-vous que Python 3 est installé :
```bash
python3 --version
```

### Erreur "Module not found"
Vérifiez que vous êtes bien dans l'environnement virtuel :
```bash
which python  # Devrait afficher /path/to/venv/bin/python
```

### Réinitialiser complètement l'environnement
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📊 Structure du venv

```
venv/
├── bin/              # Exécutables (python, pip, etc.)
├── lib/              # Paquets Python installés
├── include/          # Fichiers d'en-tête C
└── pyvenv.cfg       # Configuration du venv
```

## ✨ Configuration actuelle

**Fichiers de configuration créés** :
- `.env.example` - Template pour les variables d'environnement
- `run.sh` - Script de lancement pour macOS/Linux
- `run.bat` - Script de lancement pour Windows

**Fichiers modifiés** :
- `requirements.txt` - Ajout de `anthropic>=0.25.0`
- `README.md` - Documentation sur l'utilisation du venv
- `agents/__init__.py` - Export du module Translator
- `agents/content_analyzer.py` - Intégration de la traduction

## 🎯 Prochaines étapes

1. Créer le fichier `.env` avec votre clé API Claude :
   ```bash
   cp .env.example .env
   # Éditer .env et ajouter votre clé ANTHROPIC_API_KEY
   ```

2. Tester le système :
   ```bash
   ./run.sh --dry-run --force
   ```

3. Configurer votre `config.json` avec vos flux RSS

4. Programmer l'exécution via cron ou Planificateur de tâches (voir README.md)
