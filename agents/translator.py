"""
Translator Agent - Translates article summaries to French using Claude API
"""

import os
import re
from typing import List, Dict, Any
from anthropic import Anthropic


class Translator:
    """Translates content to French using Claude API."""

    def __init__(self):
        """Initialize the Translator with Claude API client."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic()
        self.cache = {}

    def translate_text(self, text: str, language: str = "French") -> str:
        """
        Translate text to the specified language.

        Args:
            text: Text to translate
            language: Target language (default: French)

        Returns:
            Translated text
        """
        if not text or len(text.strip()) == 0:
            return text

        # Check cache
        cache_key = f"{text[:50]}_{language}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            message = self.client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Translate the following text to {language}.
Keep the translation concise and maintain the original meaning.
Return ONLY the translated text, nothing else.

Original text:
{text}"""
                    }
                ]
            )

            translated = message.content[0].text.strip()
            self.cache[cache_key] = translated
            return translated

        except Exception as e:
            print(f"Translation error: {str(e)}")
            # Return original text if translation fails
            return text

    def translate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Translate article descriptions to French.

        Args:
            articles: List of article dictionaries

        Returns:
            Articles with translated descriptions
        """
        translated_articles = []

        for article in articles:
            article_copy = article.copy()

            # Translate description if present
            if article.get("description"):
                article_copy["description"] = self.translate_text(
                    article["description"],
                    language="French"
                )

            # Optionally translate title for better consistency
            if article.get("title"):
                # Only translate if it looks like English (optional, can be removed)
                article_copy["title"] = article["title"]

            translated_articles.append(article_copy)

        return translated_articles

    def clear_cache(self):
        """Clear translation cache."""
        self.cache = {}
