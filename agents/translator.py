"""
Translator Agent - Translates article summaries using Claude API
"""

import os
import re
from typing import List, Dict, Any
from anthropic import Anthropic
from langdetect import detect, DetectorFactory

# Set seed for consistency in language detection
DetectorFactory.seed = 0


class Translator:
    """Translates content to specified language using Claude API."""

    # Language code mappings
    LANGUAGE_CODES = {
        "French": "fr",
        "English": "en",
        "Spanish": "es",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Dutch": "nl",
        "Russian": "ru",
        "Chinese": "zh-cn",
        "Japanese": "ja",
    }

    def __init__(self):
        """Initialize the Translator with Claude API client."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic()
        self.cache = {}

    def _detect_language(self, text: str) -> str:
        """
        Detect the language of the text.

        Args:
            text: Text to detect language from

        Returns:
            Language code (e.g., 'en', 'fr', 'es')
        """
        if not text or len(text.strip()) < 10:
            return "en"  # Default to English for very short text

        try:
            return detect(text)
        except Exception:
            return "en"  # Default to English if detection fails

    def _get_language_code(self, language_name: str) -> str:
        """
        Get language code from language name.

        Args:
            language_name: Language name (e.g., 'French', 'English')

        Returns:
            Language code (e.g., 'fr', 'en')
        """
        return self.LANGUAGE_CODES.get(language_name, "fr")

    def translate_text(self, text: str, target_language: str = "French") -> str:
        """
        Translate text to the specified language only if needed.

        Args:
            text: Text to translate
            target_language: Target language name (default: French)

        Returns:
            Translated text (or original if already in target language)
        """
        if not text or len(text.strip()) == 0:
            return text

        # Detect source language
        source_lang_code = self._detect_language(text)
        target_lang_code = self._get_language_code(target_language)

        # If already in target language, return original
        if source_lang_code == target_lang_code:
            return text

        # Check cache
        cache_key = f"{text[:50]}_{target_language}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            message = self.client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Translate the following text to {target_language}.
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

    def translate_articles(
        self, articles: List[Dict[str, Any]], target_language: str = "French"
    ) -> List[Dict[str, Any]]:
        """
        Translate article descriptions to target language.

        Args:
            articles: List of article dictionaries
            target_language: Target language name (default: French)

        Returns:
            Articles with translated descriptions (only if needed)
        """
        translated_articles = []

        for article in articles:
            article_copy = article.copy()

            # Translate description if present
            if article.get("description"):
                article_copy["description"] = self.translate_text(
                    article["description"],
                    target_language=target_language
                )

            # Keep title as-is (typically proper nouns/brand names)
            if article.get("title"):
                article_copy["title"] = article["title"]

            translated_articles.append(article_copy)

        return translated_articles

    def clear_cache(self):
        """Clear translation cache."""
        self.cache = {}
