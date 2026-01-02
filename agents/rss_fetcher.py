"""
RSS Fetcher Agent - Retrieves and parses RSS feeds from configured sources
"""

import feedparser
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from email.utils import parsedate_to_datetime


class RSsFetcher:
    """Fetches and parses RSS feeds from multiple sources."""

    def __init__(self, timeout: int = 10):
        """
        Initialize the RSS Fetcher.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.articles: List[Dict[str, Any]] = []
        self.status = "not_fetched"
        self.message = ""
        self.errors: List[Dict[str, str]] = []

    def fetch_feeds(self, feeds_config: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Fetch articles from multiple RSS feeds.

        Args:
            feeds_config: List of feed configurations with name, url, and category

        Returns:
            Dict with 'status', 'message', 'articles', and 'errors'
        """
        self.articles = []
        self.errors = []

        for feed_config in feeds_config:
            self._fetch_single_feed(feed_config)

        # Deduplicate articles by link
        self.articles = self._deduplicate_articles()

        self.status = "success" if not self.errors else "partial_success"
        self.message = f"Fetched {len(self.articles)} articles from {len(feeds_config)} feeds"

        return {
            "status": self.status,
            "message": self.message,
            "articles": self.articles,
            "errors": self.errors,
            "count": len(self.articles),
        }

    def _fetch_single_feed(self, feed_config: Dict[str, str]) -> None:
        """
        Fetch a single RSS feed.

        Args:
            feed_config: Feed configuration with name, url, and category
        """
        try:
            feed_name = feed_config.get("name", "Unknown")
            feed_url = feed_config.get("url")
            category = feed_config.get("category")

            if not feed_url:
                self.errors.append({"feed": feed_name, "error": "Missing URL"})
                return

            # Set User-Agent to avoid being blocked
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            # Fetch feed with timeout
            response = requests.get(feed_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # Parse feed
            feed = feedparser.parse(response.content)

            if feed.bozo:
                # Feed parsed with errors, but still try to extract articles
                pass

            # Extract articles
            for entry in feed.entries:
                article = self._extract_article(entry, feed_name, category)
                if article:
                    self.articles.append(article)

        except requests.exceptions.Timeout:
            self.errors.append({"feed": feed_name, "error": "Timeout"})
        except requests.exceptions.ConnectionError:
            self.errors.append({"feed": feed_name, "error": "Connection error"})
        except requests.exceptions.HTTPError as e:
            self.errors.append({"feed": feed_name, "error": f"HTTP {e.response.status_code}"})
        except Exception as e:
            self.errors.append({"feed": feed_name, "error": str(e)})

    def _extract_article(
        self, entry: Any, feed_name: str, category: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract article information from a feed entry.

        Args:
            entry: Feed entry from feedparser
            feed_name: Name of the RSS feed
            category: Category of the feed

        Returns:
            Dict with article information or None if extraction fails
        """
        try:
            # Extract fields with fallbacks
            title = entry.get("title", "No title")
            link = entry.get("link", "")
            summary = entry.get("summary", "")

            # Parse publication date
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif "published" in entry:
                try:
                    pub_date = parsedate_to_datetime(entry.published)
                except:
                    pub_date = datetime.now()
            else:
                pub_date = datetime.now()

            # Clean summary (remove HTML tags)
            summary = self._clean_html(summary)

            return {
                "title": title,
                "link": link,
                "description": summary[:300],  # Limit to 300 chars
                "published": pub_date.isoformat() if pub_date else datetime.now().isoformat(),
                "source": feed_name,
                "category": category,
                "fetch_date": datetime.now().isoformat(),
            }

        except Exception:
            return None

    def _clean_html(self, text: str) -> str:
        """
        Remove HTML tags from text.

        Args:
            text: HTML text

        Returns:
            Cleaned text
        """
        import re

        # Remove HTML tags
        clean = re.compile("<.*?>")
        text = re.sub(clean, "", text)
        # Remove extra whitespace
        text = " ".join(text.split())
        return text.strip()

    def _deduplicate_articles(self) -> List[Dict[str, Any]]:
        """
        Remove duplicate articles (by link).

        Returns:
            List of unique articles
        """
        seen_links = set()
        unique_articles = []

        for article in self.articles:
            link = article.get("link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                unique_articles.append(article)
            elif not link:
                # Include articles without links
                unique_articles.append(article)

        return unique_articles

    def filter_by_date(self, articles: List[Dict[str, Any]], since: Optional[str]) -> List[Dict[str, Any]]:
        """
        Filter articles published since a specific date.

        Args:
            articles: List of articles to filter
            since: ISO format datetime string

        Returns:
            Filtered list of articles
        """
        if not since:
            return articles

        try:
            since_dt = datetime.fromisoformat(since)
            filtered = []

            for article in articles:
                pub_date = datetime.fromisoformat(article.get("published", ""))
                if pub_date > since_dt:
                    filtered.append(article)

            return filtered
        except Exception:
            return articles

    def limit_articles(self, articles: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """
        Limit the number of articles per category.

        Args:
            articles: List of articles
            limit: Maximum articles per category

        Returns:
            Limited list of articles
        """
        by_category = {}

        for article in articles:
            category = article.get("category", "Other")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(article)

        result = []
        for category, items in by_category.items():
            # Sort by publication date (newest first)
            sorted_items = sorted(items, key=lambda x: x.get("published", ""), reverse=True)
            result.extend(sorted_items[:limit])

        return result
