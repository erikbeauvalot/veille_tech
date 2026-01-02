"""
Configuration Manager Agent - Loads and saves configuration from config.json
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


class ConfigManager:
    """Manages configuration loading, saving, and validation."""

    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the Configuration Manager.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.status = "not_loaded"
        self.message = ""

    def load_config(self) -> Dict[str, str]:
        """
        Load configuration from config.json.

        Returns:
            Dict with 'status' and 'message' keys
        """
        try:
            if not os.path.exists(self.config_path):
                self.status = "error"
                self.message = f"Config file not found: {self.config_path}"
                return {"status": self.status, "message": self.message}

            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)

            # Validate structure
            if not self._validate_config():
                self.status = "error"
                return {"status": self.status, "message": "Invalid config structure"}

            self.status = "success"
            self.message = "Configuration loaded successfully"
            return {"status": self.status, "message": self.message}

        except json.JSONDecodeError as e:
            self.status = "error"
            self.message = f"Invalid JSON in config file: {str(e)}"
            return {"status": self.status, "message": self.message}
        except Exception as e:
            self.status = "error"
            self.message = f"Error loading config: {str(e)}"
            return {"status": self.status, "message": self.message}

    def save_config(self) -> Dict[str, str]:
        """
        Save current configuration to config.json.

        Returns:
            Dict with 'status' and 'message' keys
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path) or ".", exist_ok=True)

            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.status = "success"
            self.message = "Configuration saved successfully"
            return {"status": self.status, "message": self.message}

        except Exception as e:
            self.status = "error"
            self.message = f"Error saving config: {str(e)}"
            return {"status": self.status, "message": self.message}

    def _validate_config(self) -> bool:
        """
        Validate the configuration structure.

        Returns:
            True if valid, False otherwise
        """
        required_keys = ["email", "rss_feeds"]
        if not all(key in self.config for key in required_keys):
            return False

        # Validate email structure
        email_config = self.config.get("email", {})
        email_required = ["recipient", "smtp_server", "smtp_port", "sender_email", "sender_password"]
        if not all(key in email_config for key in email_required):
            return False

        # Validate RSS feeds
        rss_feeds = self.config.get("rss_feeds", [])
        if not isinstance(rss_feeds, list) or len(rss_feeds) == 0:
            return False

        for feed in rss_feeds:
            if not isinstance(feed, dict) or not all(key in feed for key in ["name", "url", "category"]):
                return False

        return True

    def get_config(self) -> Dict[str, Any]:
        """
        Get the current configuration.

        Returns:
            The configuration dictionary
        """
        return self.config.copy()

    def get_rss_feeds(self) -> list:
        """
        Get the list of RSS feed configurations.

        Returns:
            List of RSS feed configs
        """
        return self.config.get("rss_feeds", [])

    def get_email_config(self) -> Dict[str, Any]:
        """
        Get the email configuration.

        Returns:
            Email configuration dictionary
        """
        return self.config.get("email", {}).copy()

    def get_language_preference(self) -> str:
        """
        Get the language preference for article translations.

        Returns:
            Language name (e.g., 'French', 'English')
        """
        return self.config.get("language_preference", "French")

    def get_translation_provider(self) -> str:
        """
        Get the translation provider (Claude or OpenAI).

        Returns:
            Provider name (e.g., 'Claude', 'OpenAI')
        """
        return self.config.get("translation_provider", "Claude")

    def get_translation_config(self, provider: str) -> Dict[str, Any]:
        """
        Get the translation configuration for a specific provider.

        Args:
            provider: Provider name ('claude' or 'openai')

        Returns:
            Configuration dictionary for the provider
        """
        translation_config = self.config.get("translation_config", {})
        provider_lower = provider.lower()

        # Default configs for each provider (least expensive models)
        defaults = {
            "claude": {"model": "claude-opus-4-1-20250805"},
            "openai": {"model": "gpt-3.5-turbo"},
        }

        return translation_config.get(provider_lower, defaults.get(provider_lower, {}))

    def get_model_for_provider(self, provider: str) -> str:
        """
        Get the model name for a specific provider.

        Args:
            provider: Provider name ('claude' or 'openai')

        Returns:
            Model name
        """
        config = self.get_translation_config(provider)
        provider_lower = provider.lower()

        if provider_lower == "claude":
            return config.get("model", "claude-opus-4-1-20250805")
        elif provider_lower == "openai":
            return config.get("model", "gpt-3.5-turbo")
        else:
            return ""

    def update_last_execution(self) -> Dict[str, str]:
        """
        Update the last execution timestamp.

        Returns:
            Dict with 'status' and 'message' keys
        """
        try:
            self.config["last_execution"] = datetime.now().isoformat()
            return self.save_config()
        except Exception as e:
            return {"status": "error", "message": f"Error updating execution time: {str(e)}"}

    def get_last_execution(self) -> Optional[str]:
        """
        Get the last execution timestamp.

        Returns:
            ISO format timestamp or None
        """
        return self.config.get("last_execution")

    def get_max_articles_per_feed(self) -> int:
        """
        Get the maximum number of articles per feed.

        Returns:
            Max articles count (default: 5)
        """
        return self.config.get("max_articles_per_feed", 5)

    def get_rss_discovery_config(self) -> Dict[str, Any]:
        """
        Get the RSS discovery configuration.

        Returns:
            RSS discovery configuration dictionary
        """
        default_config = {
            "enabled": True,
            "max_new_feeds_per_run": 2,
            "validate_feeds": True,
            "auto_add_feeds": False,
        }
        return self.config.get("rss_discovery", default_config)

    def add_rss_feed(self, name: str, url: str, category: str) -> bool:
        """
        Add a new RSS feed to the configuration.

        Args:
            name: Feed name
            url: Feed URL
            category: Feed category

        Returns:
            True if added successfully, False if already exists
        """
        # Check if feed already exists
        existing_urls = {feed.get("url") for feed in self.config.get("rss_feeds", [])}
        if url in existing_urls:
            return False

        # Add new feed
        new_feed = {"name": name, "url": url, "category": category}
        self.config.setdefault("rss_feeds", []).append(new_feed)
        return True

    def get_log_level(self) -> str:
        """
        Get the configured log level.

        Returns:
            Log level name (ERROR, WARNING, INFO, DEBUG)
        """
        valid_levels = ["ERROR", "WARNING", "INFO", "DEBUG"]
        configured = self.config.get("log_level", "INFO").upper()

        if configured not in valid_levels:
            # Return default if invalid
            return "INFO"

        return configured
