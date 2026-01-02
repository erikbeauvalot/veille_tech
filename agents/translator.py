"""
Translator Agent - Translates article summaries using Claude or OpenAI API
"""

import os
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from langdetect import detect, DetectorFactory

# Set seed for consistency in language detection
DetectorFactory.seed = 0


class BaseTranslator(ABC):
    """Base class for translation providers."""

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
        """Initialize the translator."""
        self.cache = {}

    @abstractmethod
    def _translate_text_api(self, text: str, target_language: str) -> str:
        """Translate text using the API provider."""
        pass

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
            translated = self._translate_text_api(text, target_language)
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


class ClaudeTranslator(BaseTranslator):
    """Translator using Claude API."""

    def __init__(self):
        """Initialize Claude translator."""
        super().__init__()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        from anthropic import Anthropic
        self.client = Anthropic()

    def _translate_text_api(self, text: str, target_language: str) -> str:
        """Translate text using Claude API."""
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
        return message.content[0].text.strip()


class OpenAITranslator(BaseTranslator):
    """Translator using OpenAI API."""

    def __init__(self):
        """Initialize OpenAI translator."""
        super().__init__()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)

    def _translate_text_api(self, text: str, target_language: str) -> str:
        """Translate text using OpenAI API."""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a translator. Translate text to {target_language}. Return ONLY the translated text, nothing else."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()


class Translator:
    """Factory class for creating the appropriate translator."""

    @staticmethod
    def create(provider: str = "Claude") -> BaseTranslator:
        """
        Create a translator instance based on the provider.

        Args:
            provider: Translation provider ("Claude" or "OpenAI")

        Returns:
            Translator instance

        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower().strip()

        if provider == "claude":
            return ClaudeTranslator()
        elif provider == "openai":
            return OpenAITranslator()
        else:
            raise ValueError(
                f"Unsupported translation provider: {provider}. "
                "Choose 'Claude' or 'OpenAI'."
            )
