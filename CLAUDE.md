# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

### Setup
```bash
# Clone and enter directory
git clone https://github.com/erikbeauvalot/veille_tech.git
cd veille_tech

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

pip install -r requirements.txt

# Copy and configure
cp config.json.example config.json
cp .env.example .env
# Edit config.json and .env with your SMTP and API settings
```

### Run the System
```bash
# Standard execution (INFO level logging)
python main.py

# Verbose mode with detailed DEBUG logs
python main.py --verbose

# Test without sending email (saves to HTML file)
python main.py --dry-run

# Ignore date filter and fetch all articles
python main.py --force

# Filter articles from last N days (ignores last_execution)
python main.py --days 7           # Last 7 days
python main.py --days 30 --dry-run  # Last 30 days, test mode

# Custom log level
python main.py --log-level DEBUG

# Combine options
python main.py --days 14 --dry-run --verbose

# Using launch scripts (activates venv automatically)
./run.sh --dry-run          # macOS/Linux
run.bat --dry-run           # Windows
```

## Architecture Overview

### Multi-Agent Pipeline

The system uses a **coordinator/agent pattern** where `VeilleTechOrchestrator` (main.py) orchestrates specialized agents:

```
ConfigManager → RSSDiscovery → RSsFetcher → ContentAnalyzer → Translator → EmailSender → ErrorHandler
                                                                              (Logging)
```

**Execution Flow:**
1. Load config (ConfigManager)
2. Discover new feeds (RSSDiscovery) - optional
3. Fetch RSS feeds (RSsFetcher)
4. Filter by date and limit articles
5. Analyze, group, and translate (ContentAnalyzer + Translator)
6. Generate HTML (EmailSender)
7. Send email or save to file

### Agent Responsibilities

| Agent | File | Purpose |
|-------|------|---------|
| **ConfigManager** | `agents/config_manager.py` | Load/save config, manage feeds, track execution state |
| **RSSDiscovery** | `agents/rss_discovery.py` | Auto-discover new RSS feeds from tech sites |
| **RSsFetcher** | `agents/rss_fetcher.py` | Fetch/parse RSS feeds, deduplicate, filter articles |
| **ContentAnalyzer** | `agents/content_analyzer.py` | Group by category, generate summaries, create HTML |
| **Translator** | `agents/translator.py` | Multi-language translation (Claude/OpenAI factory) |
| **EmailSender** | `agents/email_sender.py` | Generate from templates, send via SMTP |
| **ErrorHandler** | `agents/error_handler.py` | Centralized logging, error capture, notifications |

### Key Data Structures

**Article Object:**
```python
{
    "title": str,           # Article headline
    "link": str,            # URL to full article
    "description": str,     # Summary (max 300 chars)
    "published": str,       # ISO format datetime
    "source": str,          # Feed name
    "category": str,        # AI, Cybersecurity, Cloud, etc.
    "fetch_date": str       # When fetched
}
```

**Config Hierarchy:**
- CLI flags (highest priority): `--verbose`, `--log-level`, `--dry-run`, `--force`
- Environment variables: `.env` (API keys)
- Configuration file: `config.json` (feeds, email, language, log_level)
- Defaults: Hardcoded in agent classes

## Important Implementation Details

### Logger Injection Pattern
All agents receive `logger: logging.Logger = None` parameter in `__init__`. They use:
```python
if self.logger:
    self.logger.debug(f"[AGENT_NAME] message")
```

This ensures graceful degradation if logger isn't available.

### Translation Caching
The Translator uses an in-memory cache to avoid re-translating identical text. It:
1. Detects source language
2. Skips translation if already in target language
3. Checks cache before API call
4. Falls back to original text if API fails

### RSS Fetcher Deduplication
Articles are deduplicated by link across all feeds to prevent showing the same article multiple times. This happens AFTER fetching all feeds.

### Template System
HTML emails use template placeholders (see `templates/` directory):
- `{styles}` - CSS injected from styles.css
- `{articles}` - Generated article HTML
- `{total_articles}` - Article count
- `{total_categories}` - Category count
- `{generated_time}` - Execution timestamp

### Error Handling Strategy
- RSS feed failures: Logged as WARNING, continue processing
- Network timeouts: 10-second timeout per feed
- Translation failures: Fall back to original text
- Template loading failures: Minimal HTML fallback generated
- Fatal errors: Send error email with stack trace (if configured)

## Logging System

### Log Levels
- **ERROR**: Critical failures requiring attention
- **WARNING**: Non-critical issues (feed timeouts, missing data)
- **INFO**: Operation progress and milestones
- **DEBUG**: Detailed execution flow (agent operations, API calls)

### Log Output
- **Console**: Configurable level (default: INFO)
- **File**: Always DEBUG (logs/veille_tech.log, rotating 5MB/5 backups)

### Enabling Verbose Logging
```bash
python main.py --verbose                    # DEBUG level
python main.py --log-level WARNING          # Only warnings/errors
```

### Agent Debug Logs
Each agent prefixes logs with `[AGENT_NAME]`:
- `[RSS_FETCHER]` - Feed parsing, deduplication, filtering
- `[CONTENT_ANALYZER]` - Grouping, summary generation
- `[TRANSLATOR]` - Language detection, cache hits, API calls
- `[EMAIL_SENDER]` - Template loading, SMTP connection
- `[RSS_DISCOVERY]` - Feed discovery and validation

## Configuration Essentials

### config.json Structure
```json
{
  "email": {
    "recipient": "user@example.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "sender@gmail.com",
    "sender_password": "app_password_here"
  },
  "rss_feeds": [...],
  "categories": {...},
  "language_preference": "French",
  "translation_provider": "Claude",  // or "openai"
  "translation_config": {
    "claude": {"model": "claude-opus-4-1-20250805"},
    "openai": {"model": "gpt-3.5-turbo"}
  },
  "log_level": "INFO",  // ERROR, WARNING, INFO, DEBUG
  "rss_discovery": {
    "enabled": true,
    "max_new_feeds_per_run": 2,
    "validate_feeds": true,
    "auto_add_feeds": false
  },
  "last_execution": "2026-01-02T13:36:17.535290"
}
```

### Environment Variables (.env)
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### Date Filtering Precedence
Articles are filtered based on this priority (highest → lowest):

1. **`--force` flag** - Disables ALL filtering, fetches everything
2. **`--days N` argument** - Filters to last N days, IGNORES `last_execution`
3. **`last_execution` timestamp** - Default behavior, filters since last run
4. **No filtering** - If none of the above apply

**Examples:**
```bash
python main.py --force --days 7      # ❌ Wrong: force wins, ignores --days
python main.py --days 7 --dry-run    # ✅ Correct: uses 7-day lookback
python main.py                        # ✅ Correct: uses last_execution
```

### Email Structure
The newsletter now uses an executive-friendly format:

```
┌─────────────────────────────────┐
│ Header (Date + Title)           │
├─────────────────────────────────┤
│ Table of Contents               │
│ • AI (5 articles)               │
│ • Cloud (3 articles)            │
├─────────────────────────────────┤
│ 📊 Résumés Exécutifs            │
│  AI: Summary from top 3...      │
│  Cloud: Summary from top 3...   │
├─────────────────────────────────┤
│ Articles détaillés              │
│ AI                              │
│  • Article 1 with full details  │
│  • Article 2 with full details  │
│ Cloud                           │
│  • Article 1 with full details  │
├─────────────────────────────────┤
│ Footer (Stats + Generated Time) │
└─────────────────────────────────┘
```

**Benefits:**
- Executive summary visible first for quick scanning
- Detailed articles for deeper reading
- All summaries grouped for comparison
- Clear visual separation between sections

## Common Development Tasks

### Add a New Feature
1. Identify which agent(s) need modification
2. Add logger parameter if it's a new agent
3. Update agent tests (if test file exists)
4. Add dry-run test: `python main.py --dry-run --verbose`
5. Verify logs show expected DEBUG messages
6. Commit with clear message explaining agent changes

### Debug an Issue
1. Run with verbose logging: `python main.py --verbose`
2. Check logs in `logs/veille_tech.log` for DEBUG messages
3. Review the agent responsible for that stage
4. Look for data flow in that agent's methods
5. Add print() or logger calls strategically

### Test a Single Feed
- Temporarily comment other feeds in config.json's `rss_feeds` array
- Run: `python main.py --dry-run --verbose`
- Check: `newsletter_output.html` for generated content

### Add Logging to an Agent
```python
# In agent method:
if self.logger:
    self.logger.debug(f"[AGENT_NAME] Doing something with {variable}")
```

## Critical Code Locations

| Task | Location |
|------|----------|
| Change orchestration pipeline | `main.py` VeilleTechOrchestrator.run() method |
| Modify article structure | `rss_fetcher.py` _extract_article() |
| Change HTML output structure | `agents/content_analyzer.py` generate_html() method |
| Add executive summaries | `agents/content_analyzer.py` _generate_executive_summary_section() |
| Modify email summaries | `agents/content_analyzer.py` _generate_category_summary() |
| Adjust date filtering logic | `main.py` lines 152-170 (--days vs last_execution) |
| Customize email template | `templates/newsletter.html` |
| Style email sections | `templates/styles.css` (.executive-summary, .summary-item classes) |
| Adjust log levels | Pass `--log-level` or set `config.json` log_level |
| Add RSS feed category | Update `config.json` categories and rss_feeds arrays |
| Change translation provider | `config.json` translation_provider and translation_config |
| Modify SMTP settings | `config.json` email section |

## Code Style & Patterns

### Agent Pattern (All agents follow this structure)
```python
class AgentName:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger
        self.status = "not_run"
        self.message = ""

    def main_method(self, inputs):
        if self.logger:
            self.logger.debug(f"[AGENT_NAME] Starting operation")
        # ... operation ...
        return {"status": self.status, "message": self.message, ...}
```

### Error Handling Pattern
```python
try:
    # operation
except SpecificError as e:
    self.errors.append({"resource": name, "error": str(e)})
    if self.logger:
        self.logger.warning(f"[AGENT_NAME] Error: {str(e)}")
```

### Logger Guard Pattern
```python
if self.logger:
    self.logger.debug(f"[AGENT_NAME] Debug message")
```

## Testing Approaches

### Dry-Run Testing (No Email Sent)
```bash
python main.py --dry-run
# Output: newsletter_output.html
```

### Force Full Fetch (Ignore Date Filter)
```bash
python main.py --force --dry-run
```

### Verbose Testing
```bash
python main.py --verbose --dry-run 2>&1 | grep "\[AGENT_NAME\]"
```

### Check Specific Log Level
```bash
python main.py --log-level WARNING --dry-run
```

## Troubleshooting Guide

| Problem | Solution |
|---------|----------|
| "ANTHROPIC_API_KEY not set" | Copy .env.example to .env and add your API key |
| Feeds not fetching | Check feed URLs in config.json; test with `--verbose` |
| Translation failing | Check API key is valid; verify language_preference in config |
| Email not sending | Verify SMTP settings; check logs for authentication errors; test with `--dry-run` first |
| No new articles | Normal if all articles older than last_execution; use `--force` to fetch all |
| Slow performance | Translation is slowest step; check API rate limits; reduce `max_articles_per_feed` |
| HTML template not found | Check `templates/` directory exists with .html files |

## Dependencies & Versions

Core dependencies (see `requirements.txt`):
- **feedparser**: RSS/Atom parsing
- **requests**: HTTP client (RSS fetching)
- **anthropic**: Claude API (optional, for translation)
- **openai**: OpenAI API (optional, for translation)
- **langdetect**: Language detection for smart translation
- **python-dotenv**: Environment variable loading

Python stdlib used: `logging`, `json`, `datetime`, `email.mime`, `smtplib`, `pathlib`, `time`

## Performance Considerations

1. **Translation is the slowest step** - Consider reducing `max_articles_per_feed` for faster iterations
2. **RSS Discovery runs every time** - Disable with `"enabled": false` if not needed
3. **Network timeout**: 10 seconds per feed - Adjust in RSsFetcher if needed
4. **Category summaries use API** - Falls back gracefully if Translator unavailable
5. **Email sending**: ~1-2 seconds to SMTP - Expected latency

## Git Workflow

- Commits include agent name in scope: `feat(RSsFetcher):` or `fix(Translator):`
- Breaking changes affect multiple agents (rare)
- Recent features: verbose logging, AI summaries, templates, discovery agent

## Additional Resources

- **README.md**: Full documentation and feature list
- **config.json.example**: Configuration template
- **.env.example**: Environment variables template
- **logs/veille_tech.log**: Runtime logs for debugging
- **newsletter_output.html**: Generated email preview (dry-run mode)
