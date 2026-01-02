# 📰 Veille Technologique Automatisée

Système automatisé de surveillance technologique qui récupère quotidiennement l'actualité tech (AI, cybersécurité, cloud, etc.) depuis des flux RSS, génère un résumé HTML propre et l'envoie par email.

## 🎯 Fonctionnalités

- ✅ Récupération multi-sources RSS (AI, Cybersecurity, Cloud, Tech)
- ✅ Génération HTML responsive et professionnelle
- ✅ Envoi automatique par email via SMTP (Gmail, etc.)
- ✅ Déduplication des articles
- ✅ Filtrage par date d'exécution
- ✅ Gestion robuste des erreurs et logging détaillé
- ✅ Mode dry-run pour tester sans envoyer d'email
- ✅ Notifications d'erreur automatiques
- ✅ Architecture modulaire avec agents séparés

## 📋 Architecture

Le système est basé sur une architecture multi-agents :

```
veille_tech/
├── main.py                 # Orchestrateur principal
├── agents/
│   ├── config_manager.py   # Gestion de la configuration
│   ├── rss_fetcher.py      # Récupération des flux RSS
│   ├── content_analyzer.py # Analyse et groupage des articles
│   ├── email_sender.py     # Envoi des emails
│   └── error_handler.py    # Gestion des erreurs et logs
├── config.json             # Configuration (à remplir)
├── logs/                   # Fichiers de log
├── requirements.txt        # Dépendances Python
└── README.md              # Ce fichier
```

### Agents

#### 1. Configuration Manager (`config_manager.py`)
- Charge et valide la configuration depuis `config.json`
- Sauvegarde les modifications
- Gère le timestamp de dernière exécution
- Valide la structure JSON

#### 2. RSS Fetcher (`rss_fetcher.py`)
- Récupère les flux RSS configurés
- Gère les erreurs réseau (timeouts, 404, etc.)
- Déduplique les articles
- Filtre par date si configuré
- Limite le nombre d'articles par catégorie

#### 3. Content Analyzer (`content_analyzer.py`)
- Groupe les articles par catégorie
- Génère du HTML structuré et responsive
- Extrait les informations clés (titre, lien, résumé, date)
- Crée une table des matières

#### 4. Email Sender (`email_sender.py`)
- Génère l'HTML complète du newsletter
- Envoie via SMTP (support Gmail, Outlook, etc.)
- Supporte les pièces jointes
- Gère les erreurs d'envoi
- Design responsive et professionnel

#### 5. Error Handler (`error_handler.py`)
- Capture les erreurs avec contexte
- Logging détaillé en fichier et console
- Rotation de fichiers de log (5MB max)
- Statistiques des erreurs
- Formatage pour emails d'erreur

## 🚀 Installation

### 1. Prérequis

- Python 3.8+
- pip ou conda

### 2. Cloner le projet

```bash
cd /Users/erik/Documents/Dev/AI/Claude
ls -la veille_tech/
```

### 3. Créer un environnement virtuel (recommandé)

```bash
cd veille_tech
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 5. Configurer Gmail (ou autre SMTP)

#### Pour Gmail :

1. Activer l'authentification à deux facteurs sur votre compte Google
2. Générer une **App Password** :
   - Aller sur [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Sélectionner "Mail" et "Windows/Linux"
   - Générer et copier le mot de passe généré

3. Éditer `config.json` :

```json
{
  "email": {
    "recipient": "erik@beauvalot.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "votre_email@gmail.com",
    "sender_password": "xxxxx xxxx xxxx xxxx"  # Mot de passe généré
  },
  ...
}
```

#### Pour Outlook :

```json
{
  "email": {
    "smtp_server": "smtp.office365.com",
    "smtp_port": 587,
    "sender_email": "votre_email@outlook.com",
    "sender_password": "votre_mot_de_passe"
  },
  ...
}
```

### 6. Configurer les flux RSS

Éditer `config.json` pour ajouter/modifier les flux RSS :

```json
{
  "rss_feeds": [
    {
      "name": "TechCrunch AI",
      "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
      "category": "AI"
    },
    {
      "name": "The Hacker News",
      "url": "https://feeds.feedburner.com/TheHackersNews",
      "category": "Cybersecurity"
    }
  ],
  "max_articles_per_feed": 5
}
```

## 📖 Utilisation

### Mode normal

```bash
python main.py
```

Récupère les articles depuis la dernière exécution et envoie l'email.

### Mode dry-run (test)

```bash
python main.py --dry-run
```

Génère le newsletter et le sauvegarde dans `newsletter_output.html` sans envoyer d'email.

### Mode force

```bash
python main.py --force
```

Ignore la date de dernière exécution et récupère tous les articles disponibles.

### Configuration personnalisée

```bash
python main.py --config /chemin/vers/config.json
```

### Combiner les options

```bash
python main.py --force --dry-run --config custom_config.json
```

## 📅 Programmation automatique

### Sur macOS / Linux (Cron)

Éditer crontab :

```bash
crontab -e
```

Ajouter une ligne pour exécuter quotidiennement à 9h :

```cron
0 9 * * * cd /Users/erik/Documents/Dev/AI/Claude/veille_tech && /usr/bin/python3 main.py >> logs/cron.log 2>&1
```

### Sur Windows (Planificateur de tâches)

1. Ouvrir "Planificateur de tâches"
2. Créer une tâche basique
3. Action : `C:\path\to\python.exe main.py`
4. Répertoire : `C:\path\to\veille_tech`
5. Déclencher : Quotidiennement à 9h

## 📋 Fichiers de configuration

### config.json

Structure complète :

```json
{
  "email": {
    "recipient": "erik@beauvalot.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "votre_email@gmail.com",
    "sender_password": "app_password_google"
  },
  "rss_feeds": [
    {
      "name": "Source Name",
      "url": "https://example.com/feed/",
      "category": "Category Name"
    }
  ],
  "max_articles_per_feed": 5,
  "last_execution": "2024-01-15T09:30:00.000000"
}
```

### Fichiers de log

Les logs sont stockés dans `logs/veille_tech.log` avec rotation automatique :

- **Fichier principal** : `logs/veille_tech.log` (max 5MB)
- **Archives** : `logs/veille_tech.log.1`, `.log.2`, etc.
- **Niveau console** : INFO
- **Niveau fichier** : DEBUG

## 🔒 Sécurité

### Important !

⚠️ **Ne jamais committer `config.json` avec les credentials réels !**

- Ajouter `config.json` au `.gitignore` ✓
- Utiliser des App Passwords (Gmail) et non les vrais mots de passe
- Stocker les secrets dans des variables d'environnement si possible

### Utiliser des variables d'environnement (optionnel)

```bash
export VEILLE_SMTP_PASSWORD="app_password_google"
```

Puis modifier `config.json` :

```json
{
  "sender_password": "${VEILLE_SMTP_PASSWORD}"
}
```

## 🐛 Dépannage

### Erreur : "SMTP authentication failed"

- Vérifier le mot de passe (App Password pour Gmail)
- Vérifier l'email de l'expéditeur
- S'assurer que SMTP est activé

### Erreur : "Connection refused"

- Vérifier le serveur SMTP et le port
- Gmail utilise : `smtp.gmail.com:587` (TLS)

### Aucun article reçu

- Vérifier que les flux RSS sont accessibles (utiliser `--force`)
- Vérifier les logs : `tail -f logs/veille_tech.log`
- Essayer en mode dry-run pour voir l'output

### Erreurs dans les logs

Consulter `logs/veille_tech.log` pour les détails :

```bash
# Voir les 50 dernières lignes
tail -50 logs/veille_tech.log

# Suivre les logs en temps réel
tail -f logs/veille_tech.log
```

## 📚 Sources RSS suggérées

### Intelligence Artificielle

- TechCrunch AI : https://techcrunch.com/category/artificial-intelligence/feed/
- MIT Technology Review AI : https://www.technologyreview.com/topic/artificial-intelligence/feed
- VentureBeat AI : https://venturebeat.com/category/ai/feed/

### Cybersécurité

- The Hacker News : https://feeds.feedburner.com/TheHackersNews
- Krebs on Security : https://krebsonsecurity.com/feed/
- Bleeping Computer : https://www.bleepingcomputer.com/feed/

### Cloud & DevOps

- AWS News : https://aws.amazon.com/blogs/aws/feed/
- Google Cloud Blog : https://cloudblog.withgoogle.com/rss/
- The New Stack : https://thenewstack.io/feed/

### Tech General

- Ars Technica : https://feeds.arstechnica.com/arstechnica/index
- The Verge : https://www.theverge.com/rss/index.xml
- Wired : https://www.wired.com/feed/rss

## 🧪 Tests

### Test de la configuration

```bash
python -c "from agents import ConfigManager; cm = ConfigManager(); print(cm.load_config())"
```

### Test des flux RSS

```bash
python -c "
from agents import ConfigManager, RSsFetcher
cm = ConfigManager()
cm.load_config()
fetcher = RSsFetcher()
result = fetcher.fetch_feeds(cm.get_rss_feeds())
print(f'Status: {result[\"status\"]}')
print(f'Articles: {result[\"count\"]}')
"
```

### Test de l'email

```bash
python main.py --dry-run --force
# Vérifier newsletter_output.html
```

## 📊 Structure des données

### Articles

Chaque article a la structure suivante :

```python
{
    "title": str,              # Titre de l'article
    "link": str,               # URL de l'article
    "description": str,        # Résumé (max 300 caractères)
    "published": str,          # ISO timestamp
    "source": str,             # Nom du flux RSS
    "category": str,           # Catégorie
    "fetch_date": str          # ISO timestamp
}
```

### Résultat d'exécution

```python
{
    "status": "success|error|partial_success",
    "message": str,
    "articles_count": int,
    "categories_count": int,
    "dry_run": bool,
    "log_file": str  # Si erreur
}
```

## 🤝 Contribuer

Les améliorations suggérées :

- [ ] Interface web pour gérer la config
- [ ] Statistiques hebdomadaires
- [ ] Détection de trending topics
- [ ] Support Slack/Discord
- [ ] Filtrage par langage
- [ ] Résumé avec IA (GPT, Claude, etc.)

## 📝 License

MIT

## ✉️ Support

Pour les problèmes :

1. Consulter les logs : `logs/veille_tech.log`
2. Essayer en mode dry-run : `python main.py --dry-run`
3. Vérifier la configuration : `config.json`

---

**Créé avec ❤️ pour l'automatisation de la veille technologique**
