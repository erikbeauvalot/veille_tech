# 📰 Veille Technologique Automatisée

Système automatisé de surveillance technologique qui récupère quotidiennement l'actualité tech (AI, cybersécurité, cloud, etc.) depuis des flux RSS, génère un résumé HTML propre et l'envoie par email.

## 🎯 Fonctionnalités

- ✅ Récupération multi-sources RSS (AI, Cybersecurity, Cloud, Tech)
- ✅ **Découverte automatique de nouveaux flux RSS** à chaque exécution
- ✅ **Traduction automatique des résumés en français** via Claude API
- ✅ Génération HTML responsive et professionnelle
- ✅ Envoi automatique par email via SMTP (Gmail, etc.)
- ✅ Déduplication des articles
- ✅ Filtrage par date d'exécution
- ✅ Gestion robuste des erreurs et logging détaillé
- ✅ Mode dry-run pour tester sans envoyer d'email
- ✅ Notifications d'erreur automatiques
- ✅ Architecture modulaire avec 7 agents séparés

## 📋 Architecture

Le système est basé sur une architecture multi-agents :

```
veille_tech/
├── main.py                 # Orchestrateur principal
├── agents/
│   ├── config_manager.py   # Gestion de la configuration
│   ├── rss_discovery.py    # Découverte automatique de nouveaux flux
│   ├── rss_fetcher.py      # Récupération des flux RSS
│   ├── content_analyzer.py # Analyse et groupage des articles
│   ├── translator.py       # Traduction en français via Claude API
│   ├── email_sender.py     # Envoi des emails
│   └── error_handler.py    # Gestion des erreurs et logs
├── config.json             # Configuration (à remplir)
├── .env.example            # Template pour les variables d'environnement
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
- Ajoute de nouveaux flux à la configuration

#### 2. Translator (`translator.py`) ⭐ NEW
- Traduit automatiquement les résumés des articles en français
- Utilise l'API Claude pour des traductions de qualité
- Cache les traductions pour optimiser les appels API
- S'active automatiquement si la clé API est configurée
- Gracefully dégradé : fonctionnement normal sans traduction si API key manquante

#### 3. RSS Discovery (`rss_discovery.py`) ⭐ NEW
- Découvre automatiquement de nouveaux flux RSS intéressants
- Teste une base de sites tech populaires (TechCrunch, VentureBeat, etc.)
- Valide l'accessibilité des flux avant de les ajouter
- Catégorise automatiquement les flux (AI, Cybersecurity, Cloud, Dev, Tech)
- Évite les doublons avec les flux existants
- S'exécute au début de chaque run pour enrichir vos sources
- Modes : "notification" (logs) ou "auto-add" (ajout automatique)

#### 4. RSS Fetcher (`rss_fetcher.py`)
- Récupère les flux RSS configurés
- Gère les erreurs réseau (timeouts, 404, etc.)
- Déduplique les articles
- Filtre par date si configuré
- Limite le nombre d'articles par catégorie

#### 5. Content Analyzer (`content_analyzer.py`)
- Groupe les articles par catégorie
- Génère du HTML structuré et responsive
- Extrait les informations clés (titre, lien, résumé, date)
- Crée une table des matières
- Intègre la traduction en français via le Translator

#### 6. Email Sender (`email_sender.py`)
- Génère l'HTML complète du newsletter
- Envoie via SMTP (support Gmail, Outlook, etc.)
- Supporte les pièces jointes
- Gère les erreurs d'envoi
- Design responsive et professionnel

#### 7. Error Handler (`error_handler.py`)
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

### 3. Créer un environnement virtuel

```bash
cd veille_tech
python3 -m venv venv
```

### 4. Installer les dépendances

L'environnement virtuel a été créé. Les dépendances sont prêtes à être installées via le script :

**macOS / Linux :**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Windows :**
```cmd
venv\Scripts\activate.bat
pip install -r requirements.txt
```

Ou plus simplement, utilisez les scripts fournis (voir la section "Utilisation" ci-dessous).

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
  "max_articles_per_feed": 5,
  "rss_discovery": {
    "enabled": true,
    "max_new_feeds_per_run": 2,
    "validate_feeds": true,
    "auto_add_feeds": false
  }
}
```

### 7. Configurer la Traduction multilingue ⭐ UPDATED

Le système traduit automatiquement tous les résumés des articles dans la langue de votre choix en utilisant **Claude ou OpenAI**.

#### Configuration des clés API

1. Créer un fichier `.env` à la racine du projet (ou copier depuis `.env.example`) :

```bash
cp .env.example .env
```

2. Ajouter vos clés API (au moins une) :

```env
# Pour Claude
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# Pour OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here
```

3. La traduction s'activera automatiquement au prochain lancement

#### Choisir le provider et le modèle de traduction

Éditer `config.json` et configurer :

```json
{
  "language_preference": "French",
  "translation_provider": "Claude",
  "translation_config": {
    "claude": {
      "model": "claude-3-haiku-20250307"
    },
    "openai": {
      "model": "gpt-3.5-turbo"
    }
  }
}
```

**Providers et modèles disponibles** :

**Claude** (par défaut - moins cher) :
- `claude-3-haiku-20250307` ⭐ (recommandé - moins cher)
- `claude-3-sonnet-20250219` (équilibre qualité/prix)
- `claude-3-5-sonnet-20241022` (plus puissant)
- `claude-opus-4-1-20250805` (le plus puissant)

**OpenAI** :
- `gpt-3.5-turbo` ⭐ (recommandé - moins cher)
- `gpt-4` (plus puissant)
- `gpt-4-turbo` (plus rapide que GPT-4)
- `gpt-4o` (optimisé)

#### Choisir la langue de traduction

Le champ `language_preference` dans `config.json` :

```json
{
  "language_preference": "French",
  ...
}
```

**Langues supportées** :
- `French` (Français)
- `English` (Anglais)
- `Spanish` (Espagnol)
- `German` (Allemand)
- `Italian` (Italien)
- `Portuguese` (Portugais)
- `Dutch` (Néerlandais)
- `Russian` (Russe)
- `Chinese` (Chinois)
- `Japanese` (Japonais)

#### Obtenir vos clés API

**Claude** :
1. Aller sur [console.anthropic.com](https://console.anthropic.com)
2. Aller à l'onglet "API Keys"
3. Créer une nouvelle clé
4. Copier dans `.env`

**OpenAI** :
1. Aller sur [platform.openai.com](https://platform.openai.com/api-keys)
2. Créer une nouvelle clé
3. Copier dans `.env`

**Comportement intelligent** :
- ✅ Si les articles sont déjà dans la langue choisie → Pas de traduction (économie API)
- ✅ Si articles dans autre langue → Traduction automatique
- ✅ Cache des traductions pour optimiser les appels API

**Note** : Sans clé API du provider configuré, le système fonctionne normalement mais les résumés restent en anglais (texte original des flux RSS).

### 8. Configurer la Découverte Automatique de Flux RSS ⭐

La découverte automatique teste des sites tech populaires et vous propose de nouveaux flux RSS :

```json
{
  "rss_discovery": {
    "enabled": true,
    "max_new_feeds_per_run": 2,
    "validate_feeds": true,
    "auto_add_feeds": false
  }
}
```

**Paramètres** :
- `enabled` (bool) : Active/désactive la découverte (défaut: `true`)
- `max_new_feeds_per_run` (int) : Maximum de nouveaux flux à découvrir par exécution (défaut: `2`)
- `validate_feeds` (bool) : Valide que les flux sont accessibles avant de les proposer (défaut: `true`)
- `auto_add_feeds` (bool) : Ajoute automatiquement les nouveaux flux trouvés à la config (défaut: `false`)
  - `false` : Les nouveaux flux sont listés dans les logs pour votre review
  - `true` : Les nouveaux flux sont ajoutés automatiquement au config.json

**Exemple avec auto-add activé** :

```json
{
  "rss_discovery": {
    "enabled": true,
    "max_new_feeds_per_run": 3,
    "validate_feeds": true,
    "auto_add_feeds": true
  }
}
```

À chaque exécution, le système découvrira automatiquement jusqu'à 3 nouveaux flux intéressants et les ajoutera au config.json. Les logs vous montreront les flux découverts et ajoutés.

## 📖 Utilisation

⚠️ **IMPORTANT** : Toutes les exécutions doivent se faire dans l'environnement virtuel.

### Scripts de lancement rapide

#### macOS / Linux
```bash
./run.sh                          # Mode normal
./run.sh --dry-run               # Mode dry-run
./run.sh --force                 # Mode force
./run.sh --force --dry-run       # Combiner les options
```

#### Windows
```cmd
run.bat                          # Mode normal
run.bat --dry-run               # Mode dry-run
run.bat --force                 # Mode force
run.bat --force --dry-run       # Combiner les options
```

### Activation manuelle du venv

Si vous préférez activer manuellement :

**macOS / Linux :**
```bash
source venv/bin/activate
python main.py --dry-run
deactivate  # Quitter l'environnement quand fini
```

**Windows :**
```cmd
venv\Scripts\activate.bat
python main.py --dry-run
deactivate  # Quitter l'environnement quand fini
```

### Options disponibles

- **Mode normal** : `python main.py` - Récupère les articles depuis la dernière exécution et envoie l'email (si articles trouvés)
- **Mode dry-run** : `python main.py --dry-run` - Génère le newsletter et le sauvegarde dans `newsletter_output.html` sans envoyer d'email
- **Mode force** : `python main.py --force` - Ignore la date de dernière exécution et récupère tous les articles disponibles
- **Configuration personnalisée** : `python main.py --config /chemin/vers/config.json`
- **Combiner les options** : `python main.py --force --dry-run --config custom_config.json`

### Logique d'envoi

⚠️ **Important** : L'email ne sera envoyé QUE s'il y a au moins un nouvel article :
- ✅ Articles trouvés → Email envoyé avec les articles
- ❌ Pas d'article → Email non envoyé, timestamp d'exécution mis à jour quand même

Cela évite d'envoyer des newsletters vides. Le timestamp `last_execution` est toujours mis à jour pour éviter de re-traiter les mêmes périodes.

## 📅 Programmation automatique

### Sur macOS / Linux (Cron)

Éditer crontab :

```bash
crontab -e
```

Ajouter une ligne pour exécuter quotidiennement à 9h (utilise le script qui gère l'activation du venv) :

```cron
0 9 * * * cd /Users/erik/Documents/Dev/AI/Claude/veille_tech && ./run.sh >> logs/cron.log 2>&1
```

Ou si vous préférez contrôler l'activation manuellement :

```cron
0 9 * * * cd /Users/erik/Documents/Dev/AI/Claude/veille_tech && source venv/bin/activate && python main.py >> logs/cron.log 2>&1
```

### Sur Windows (Planificateur de tâches)

1. Ouvrir "Planificateur de tâches"
2. Créer une tâche basique
3. Action : `C:\path\to\veille_tech\run.bat` (ou `python.exe main.py` si vous préférez)
4. Répertoire : `C:\path\to\veille_tech`
5. Déclencher : Quotidiennement à 9h

**Recommandé** : Utiliser `run.bat` qui gère automatiquement l'activation du venv

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
  "language_preference": "French",
  "translation_provider": "Claude",
  "translation_config": {
    "claude": {
      "model": "claude-3-haiku-20250307"
    },
    "openai": {
      "model": "gpt-3.5-turbo"
    }
  },
  "rss_discovery": {
    "enabled": true,
    "max_new_feeds_per_run": 2,
    "validate_feeds": true,
    "auto_add_feeds": false
  },
  "last_execution": "2024-01-15T09:30:00.000000"
}
```

**Champs** :
- `email` : Configuration SMTP pour l'envoi d'emails
- `rss_feeds` : Liste des flux RSS à surveiller
- `max_articles_per_feed` : Nombre max d'articles par catégorie
- `language_preference` : Langue pour les traductions (French, English, Spanish, etc.)
- `translation_provider` : Fournisseur de traduction (Claude ou OpenAI)
- `translation_config` : Configuration du modèle pour chaque provider
  - `claude.model` : Modèle Claude à utiliser (défaut: claude-3-haiku)
  - `openai.model` : Modèle OpenAI à utiliser (défaut: gpt-3.5-turbo)
- `rss_discovery` : Configuration de la découverte automatique de flux
- `last_execution` : Timestamp de la dernière exécution (auto-updated)

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
- [x] Résumé avec IA (Claude) - Traduction en français via Claude API

## 📝 License

MIT

## ✉️ Support

Pour les problèmes :

1. Consulter les logs : `logs/veille_tech.log`
2. Essayer en mode dry-run : `python main.py --dry-run`
3. Vérifier la configuration : `config.json`

---

**Créé avec ❤️ pour l'automatisation de la veille technologique**
