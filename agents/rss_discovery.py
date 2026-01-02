"""
RSS Discovery Agent - Automatically discovers new interesting RSS feeds
"""

import requests
import feedparser
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re


class RSSDiscovery:
    """Discovers and validates new RSS feeds automatically."""

    def __init__(self, timeout: int = 10):
        """
        Initialize the RSS Discovery agent.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.discovered_feeds: List[Dict[str, str]] = []
        self.status = "not_run"
        self.message = ""

        # Known tech sites and their potential RSS patterns
        self.tech_sites = [
            # AI & Machine Learning
            {"domain": "venturebeat.com", "category": "AI", "patterns": ["/category/ai/feed/"]},
            {"domain": "artificialintelligence-news.com", "category": "AI", "patterns": ["/feed/"]},
            {"domain": "deeplearning.ai", "category": "AI", "patterns": ["/blog/feed/"]},

            # Cybersecurity
            {"domain": "thehackernews.com", "category": "Cybersecurity", "patterns": ["/feeds/posts/default"]},
            {"domain": "darkreading.com", "category": "Cybersecurity", "patterns": ["/rss.xml", "/rss/all.xml"]},
            {"domain": "cybersecuritynews.com", "category": "Cybersecurity", "patterns": ["/feed/"]},
            {"domain": "threatpost.com", "category": "Cybersecurity", "patterns": ["/feed/"]},

            # Cloud & DevOps
            {"domain": "thenewstack.io", "category": "Cloud", "patterns": ["/feed/"]},
            {"domain": "devops.com", "category": "Cloud", "patterns": ["/feed/"]},
            {"domain": "cloudblog.withgoogle.com", "category": "Cloud", "patterns": ["/rss/"]},

            # General Tech
            {"domain": "wired.com", "category": "Tech", "patterns": ["/feed/rss"]},
            {"domain": "engadget.com", "category": "Tech", "patterns": ["/rss.xml"]},
            {"domain": "zdnet.com", "category": "Tech", "patterns": ["/rss.xml"]},
            {"domain": "cnet.com", "category": "Tech", "patterns": ["/rss/news/"]},

            # Startups & Business
            {"domain": "techmeme.com", "category": "Tech", "patterns": ["/feed.xml"]},
            {"domain": "siliconangle.com", "category": "Tech", "patterns": ["/feed/"]},

            # Developer News
            {"domain": "dev.to", "category": "Dev", "patterns": ["/feed"]},
            {"domain": "hackernoon.com", "category": "Dev", "patterns": ["/feed"]},
        ]

    def discover_feeds(
        self,
        existing_feeds: List[Dict[str, str]],
        max_new_feeds: int = 5,
        validate: bool = True,
    ) -> Dict[str, Any]:
        """
        Discover new RSS feeds that aren't already in the configuration.

        Args:
            existing_feeds: List of currently configured feeds
            max_new_feeds: Maximum number of new feeds to discover
            validate: Whether to validate feeds before adding

        Returns:
            Dict with discovery results
        """
        self.discovered_feeds = []
        existing_urls = {feed.get("url") for feed in existing_feeds}

        # Track discovered count
        discovered_count = 0

        for site in self.tech_sites:
            if discovered_count >= max_new_feeds:
                break

            domain = site["domain"]
            category = site["category"]
            patterns = site["patterns"]

            for pattern in patterns:
                if discovered_count >= max_new_feeds:
                    break

                # Construct feed URL
                feed_url = f"https://{domain}{pattern}"

                # Skip if already exists
                if feed_url in existing_urls:
                    continue

                # Validate feed if requested
                if validate:
                    feed_info = self._validate_feed(feed_url, category)
                    if feed_info:
                        self.discovered_feeds.append(feed_info)
                        existing_urls.add(feed_url)
                        discovered_count += 1
                else:
                    # Add without validation
                    self.discovered_feeds.append({
                        "name": self._extract_site_name(domain),
                        "url": feed_url,
                        "category": category,
                    })
                    discovered_count += 1

        self.status = "success"
        self.message = f"Discovered {len(self.discovered_feeds)} new feeds"

        return {
            "status": self.status,
            "message": self.message,
            "discovered_feeds": self.discovered_feeds,
            "count": len(self.discovered_feeds),
        }

    def _validate_feed(self, feed_url: str, category: str) -> Optional[Dict[str, str]]:
        """
        Validate that a feed URL is accessible and parseable.

        Args:
            feed_url: URL of the RSS feed
            category: Category for the feed

        Returns:
            Feed info dict if valid, None otherwise
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            # Fetch feed
            response = requests.get(feed_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # Parse feed
            feed = feedparser.parse(response.content)

            # Check if feed is valid (has entries)
            if not feed.entries or len(feed.entries) == 0:
                return None

            # Extract feed title or derive from URL
            feed_title = feed.feed.get("title", "")
            if not feed_title:
                feed_title = self._extract_site_name(urlparse(feed_url).netloc)

            return {
                "name": feed_title,
                "url": feed_url,
                "category": category,
            }

        except Exception:
            return None

    def _extract_site_name(self, domain: str) -> str:
        """
        Extract a readable site name from a domain.

        Args:
            domain: Domain name

        Returns:
            Formatted site name
        """
        # Remove www. and TLD
        name = domain.replace("www.", "")
        name = re.sub(r"\.(com|net|org|io|ai)$", "", name)

        # Capitalize words
        words = name.split(".")
        if words:
            name = words[0]

        # Convert from camelCase or snake_case
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        name = name.replace("_", " ").replace("-", " ")

        # Capitalize
        return " ".join(word.capitalize() for word in name.split())

    def auto_categorize(self, feed_url: str, feed_content: str) -> str:
        """
        Automatically categorize a feed based on content.

        Args:
            feed_url: URL of the feed
            feed_content: Content/title of feed entries

        Returns:
            Suggested category
        """
        content_lower = feed_content.lower()

        # AI keywords
        ai_keywords = ["artificial intelligence", "machine learning", "deep learning",
                       "neural network", "ai", "ml", "gpt", "llm", "chatbot"]
        if any(keyword in content_lower for keyword in ai_keywords):
            return "AI"

        # Cybersecurity keywords
        security_keywords = ["security", "hacker", "vulnerability", "breach", "malware",
                            "ransomware", "cyber", "threat", "exploit"]
        if any(keyword in content_lower for keyword in security_keywords):
            return "Cybersecurity"

        # Cloud keywords
        cloud_keywords = ["cloud", "aws", "azure", "kubernetes", "docker", "devops",
                         "serverless", "infrastructure"]
        if any(keyword in content_lower for keyword in cloud_keywords):
            return "Cloud"

        # Developer keywords
        dev_keywords = ["programming", "coding", "developer", "software", "github",
                       "python", "javascript", "java"]
        if any(keyword in content_lower for keyword in dev_keywords):
            return "Dev"

        # Default
        return "Tech"

    def search_feeds_on_site(self, site_url: str) -> List[str]:
        """
        Search for RSS feeds on a given website.

        Args:
            site_url: URL of the website to search

        Returns:
            List of discovered feed URLs
        """
        discovered = []

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            # Fetch the site
            response = requests.get(site_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            # Look for feed links in HTML
            feed_patterns = [
                r'<link[^>]+type=["\']application/rss\+xml["\'][^>]+href=["\']([^"\']+)["\']',
                r'<link[^>]+type=["\']application/atom\+xml["\'][^>]+href=["\']([^"\']+)["\']',
                r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/rss\+xml["\']',
            ]

            for pattern in feed_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                for match in matches:
                    feed_url = urljoin(site_url, match)
                    if feed_url not in discovered:
                        discovered.append(feed_url)

            # Try common feed paths
            common_paths = ["/feed", "/rss", "/feed.xml", "/rss.xml", "/atom.xml", "/blog/feed"]
            for path in common_paths:
                feed_url = urljoin(site_url, path)
                if feed_url not in discovered:
                    # Quick validation
                    try:
                        r = requests.head(feed_url, headers=headers, timeout=5)
                        if r.status_code == 200:
                            discovered.append(feed_url)
                    except:
                        pass

        except Exception:
            pass

        return discovered

    def get_feed_statistics(self, feed_url: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics about a feed (article count, update frequency, etc.).

        Args:
            feed_url: URL of the RSS feed

        Returns:
            Statistics dictionary or None
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(feed_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            feed = feedparser.parse(response.content)

            return {
                "title": feed.feed.get("title", "Unknown"),
                "total_entries": len(feed.entries),
                "has_entries": len(feed.entries) > 0,
                "latest_entry_date": feed.entries[0].get("published", "Unknown") if feed.entries else None,
            }

        except Exception:
            return None
