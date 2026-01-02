# 🆕 RSS Discovery Agent - Résumé des Changements

## Qu'est-ce qui a été ajouté ?

Un nouvel agent de **découverte automatique de flux RSS** qui s'exécute au début de chaque exécution pour enrichir vos sources de nouvelles.

## ✨ Fonctionnalités

### Agent RSS Discovery (`agents/rss_discovery.py`)
- ✅ Découverte automatique de nouveaux flux RSS intéressants
- ✅ Base de sites tech populaires pré-configurés (15+ domaines)
- ✅ Validation automatique de l'accessibilité des flux
- ✅ Catégorisation intelligente (AI, Cybersecurity, Cloud, Dev, Tech)
- ✅ Évite les doublons avec les flux existants
- ✅ Deux modes de fonctionnement :
  - **Notification mode** (défaut) : Logs les nouveaux flux trouvés
  - **Auto-add mode** : Ajoute automatiquement au config.json

## 📋 Fichiers Modifiés/Créés

### Nouveaux fichiers
```
agents/rss_discovery.py          (320 lignes) - L'agent de découverte
RSS_DISCOVERY_SUMMARY.md          (Ce fichier)
```

### Fichiers modifiés
```
agents/__init__.py                - Import du nouvel agent
agents/config_manager.py          - Nouvelles méthodes pour gérer les flux
main.py                           - Intégration de l'agent dans le pipeline
config.json                       - Nouvelle section "rss_discovery"
README.md                         - Documentation complète
```

## 🔧 Configuration

### Configuration par défaut

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

### Paramètres

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `enabled` | bool | `true` | Active/désactive la découverte |
| `max_new_feeds_per_run` | int | `2` | Max de flux à découvrir par exécution |
| `validate_feeds` | bool | `true` | Valide l'accessibilité des flux |
| `auto_add_feeds` | bool | `false` | Ajoute automatiquement au config |

## 📖 Exemples d'Utilisation

### Mode 1 : Notification (Recommandé)
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

**Comportement** : Les nouveaux flux sont listés dans les logs. Vous décidez manuellement lesquels ajouter.

**Logs** :
```
[RSS_DISCOVERY] Discovered 2 new feeds
[RSS_DISCOVERY]   - darkreading (Cybersecurity): https://darkreading.com/rss.xml
[RSS_DISCOVERY]   - Threatpost (Cybersecurity): https://threatpost.com/feed/
```

### Mode 2 : Auto-add
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

**Comportement** : Les nouveaux flux sont automatiquement ajoutés au config.json.

**Logs** :
```
[RSS_DISCOVERY] Discovered 2 new feeds
[RSS_DISCOVERY] Added new feed: darkreading
[RSS_DISCOVERY] Added new feed: Threatpost
```

### Mode 3 : Découverte sans validation
```json
{
  "rss_discovery": {
    "enabled": true,
    "max_new_feeds_per_run": 5,
    "validate_feeds": false,
    "auto_add_feeds": false
  }
}
```

**Comportement** : Plus rapide mais peut ajouter des flux inaccessibles.

## 🔍 Sites Testés Automatiquement

L'agent teste ces catégories de sites :

### AI & Machine Learning
- venturebeat.com
- artificialintelligence-news.com
- deeplearning.ai

### Cybersecurity
- thehackernews.com
- darkreading.com
- cybersecuritynews.com
- threatpost.com

### Cloud & DevOps
- thenewstack.io
- devops.com
- cloudblog.withgoogle.com

### General Tech
- wired.com
- engadget.com
- zdnet.com
- cnet.com

### Startups & Business
- techmeme.com
- siliconangle.com

### Developer News
- dev.to
- hackernoon.com

## 📊 Flux du Pipeline

Le pipeline d'exécution est maintenant :

```
1. Load Configuration
   ↓
2. [NEW] Discover RSS Feeds ← Agent RSS Discovery
   ↓
3. Fetch RSS Feeds ← Agent RSS Fetcher
   ↓
4. Filter by Date
   ↓
5. Limit per Category
   ↓
6. Analyze & Group ← Agent Content Analyzer
   ↓
7. Generate HTML
   ↓
8. Create Email
   ↓
9. Send Email ← Agent Email Sender
   ↓
10. Update Last Execution
```

## 🎯 Cas d'Usage

### Cas 1 : Croissance Progressive des Sources
```json
{
  "rss_discovery": {
    "enabled": true,
    "max_new_feeds_per_run": 1,
    "validate_feeds": true,
    "auto_add_feeds": true
  }
}
```

Ajoute 1 nouveau flux par jour → ~30 nouveaux flux par mois

### Cas 2 : Veille Continue
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

Propose 2 flux par exécution → Vous contrôlez les ajouts

### Cas 3 : Découverte Agressive
```json
{
  "rss_discovery": {
    "enabled": true,
    "max_new_feeds_per_run": 5,
    "validate_feeds": true,
    "auto_add_feeds": true
  }
}
```

Ajoute jusqu'à 5 flux par exécution → Croissance rapide

## 🔒 Sécurité & Considérations

- **Pas d'API externe** : Utilise uniquement `requests` et `feedparser` standard
- **Évite les doublons** : Vérifie l'URL avant d'ajouter
- **Validation optionnelle** : Peut vérifier l'accessibilité pour éviter les liens morts
- **Logs détaillés** : Tous les flux découverts sont loggés

## ⚙️ Intégration avec le Reste du Système

L'agent RSS Discovery s'intègre parfaitement :
- ✅ Utilise `ConfigManager` pour charger/sauvegarder la config
- ✅ Utilise `ErrorHandler` pour le logging
- ✅ Ajoute les flux trouvés à la liste existante
- ✅ Ne bloque pas le pipeline si erreur

## 📝 Exemples de Logs

### Découverte réussie
```
02/01/2026 09:05:09 - veille_tech - INFO - [ORCHESTRATOR] Discovering new RSS feeds...
02/01/2026 09:05:11 - veille_tech - INFO - [RSS_DISCOVERY] Discovered 2 new feeds
02/01/2026 09:05:11 - veille_tech - INFO - [RSS_DISCOVERY] New feeds discovered but auto_add_feeds is disabled. Review in logs and add manually if interested.
02/01/2026 09:05:11 - veille_tech - INFO - [RSS_DISCOVERY]   - darkreading (Cybersecurity): https://darkreading.com/rss.xml
02/01/2026 09:05:11 - veille_tech - INFO - [RSS_DISCOVERY]   - Threatpost (Cybersecurity): https://threatpost.com/feed/
```

### Auto-add activé
```
02/01/2026 09:03:17 - veille_tech - INFO - [RSS_DISCOVERY] Discovered 1 new feeds
02/01/2026 09:03:17 - veille_tech - INFO - [RSS_DISCOVERY] Added new feed: The Hacker News
```

## 🚀 Prochaines Étapes Recommandées

1. **Testez le mode notification** : Vérifiez que la découverte fonctionne
   ```bash
   python3 main.py --dry-run --force
   ```

2. **Revoyez les flux découverts** : Consultez les logs
   ```bash
   grep "RSS_DISCOVERY" logs/veille_tech.log
   ```

3. **Activez auto-add si souhaité** : Modifiez config.json
   ```json
   "auto_add_feeds": true
   ```

4. **Testez l'ajout automatique** : Vérifiez que config.json se met à jour
   ```bash
   python3 main.py --dry-run --force
   cat config.json | grep "url" | wc -l
   ```

## 📚 Documentation Complète

Voir `README.md` pour :
- Configuration détaillée
- Exemples d'utilisation
- Dépannage
- Configuration de l'email
- Programmation automatique (cron)

## ✅ Tests Effectués

- ✅ Mode notification (découverte + logs)
- ✅ Mode auto-add (ajout automatique au config)
- ✅ Détection de doublons (ne réajoute pas des flux existants)
- ✅ Validation des flux (vérifie l'accessibilité)
- ✅ Intégration au pipeline complet
- ✅ Logs détaillés et informatifs

---

**Créé le** : 02/01/2026
**Statut** : ✅ Production Ready
