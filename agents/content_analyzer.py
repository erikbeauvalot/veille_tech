"""
Content Analyzer & Summarizer Agent - Groups articles and generates HTML summary
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
import re
from .translator import Translator


class ContentAnalyzer:
    """Analyzes content and groups articles by category."""

    def __init__(self, provider: str = "Claude", model: str = None, logger: logging.Logger = None):
        """
        Initialize the Content Analyzer.

        Args:
            provider: Translation provider ("Claude" or "OpenAI")
            model: Model to use (optional, uses defaults if not specified)
            logger: Logger instance for logging
        """
        self.logger = logger
        self.grouped_articles: Dict[str, List[Dict[str, Any]]] = {}
        self.status = "not_analyzed"
        self.message = ""
        self.translation_provider = provider
        self.translation_model = model
        self.target_language = "French"  # Default target language
        try:
            self.translator = Translator.create(provider, model=model, logger=self.logger)
        except ValueError as e:
            # If API key not set or invalid provider, translator will be None
            self.translator = None
            if self.logger:
                self.logger.warning(f"[CONTENT_ANALYZER] Translation disabled: {str(e)}")
            else:
                print(f"Translation disabled: {str(e)}")

    def analyze_and_group(
        self, articles: List[Dict[str, Any]], target_language: str = "French"
    ) -> Dict[str, Any]:
        """
        Analyze articles and group by category.

        Args:
            articles: List of articles from RSS Fetcher
            target_language: Target language for translation (default: French)

        Returns:
            Dict with grouped articles and analysis results
        """
        try:
            # Store target language for use in summary generation
            self.target_language = target_language

            # Translate article descriptions if translator is available
            if self.translator:
                articles = self.translator.translate_articles(articles, target_language=target_language)

            self.grouped_articles = self._group_by_category(articles)

            # Sort categories and articles
            for category in self.grouped_articles:
                self.grouped_articles[category] = sorted(
                    self.grouped_articles[category],
                    key=lambda x: x.get("published", ""),
                    reverse=True,
                )

            self.status = "success"
            self.message = f"Analyzed {len(articles)} articles across {len(self.grouped_articles)} categories"

            return {
                "status": self.status,
                "message": self.message,
                "grouped_articles": self.grouped_articles,
                "total_articles": len(articles),
                "total_categories": len(self.grouped_articles),
            }

        except Exception as e:
            self.status = "error"
            self.message = f"Error analyzing content: {str(e)}"
            return {"status": self.status, "message": self.message}

    def _group_by_category(self, articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group articles by their category.

        Args:
            articles: List of articles

        Returns:
            Dictionary with categories as keys and article lists as values
        """
        grouped = {}

        for article in articles:
            category = article.get("category", "Other")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(article)

        return grouped

    def generate_category_summaries(self, grouped_articles: Dict[str, List[Dict[str, Any]]]) -> Dict[str, str]:
        """
        Generate executive summaries for all categories.

        Args:
            grouped_articles: Articles grouped by category

        Returns:
            Dict mapping category name to summary text
        """
        summaries = {}
        for category, articles in grouped_articles.items():
            summary = self._generate_category_summary(articles)
            if summary:
                summaries[category] = summary
        return summaries

    def generate_html(self, grouped_articles: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Generate HTML summary from grouped articles.

        Format: TOC → Executive Summaries → Detailed Articles

        Args:
            grouped_articles: Articles grouped by category

        Returns:
            Complete HTML content
        """
        html_content = ""

        # Generate table of contents
        html_content += self._generate_toc(grouped_articles)

        # Generate executive summary section (all category summaries together)
        html_content += self._generate_executive_summary_section(grouped_articles)

        # Generate detailed article sections (by category, without summaries)
        for category, articles in grouped_articles.items():
            html_content += self._generate_category_section(category, articles)

        return html_content

    def _generate_toc(self, grouped_articles: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Generate table of contents.

        Args:
            grouped_articles: Articles grouped by category

        Returns:
            HTML for table of contents
        """
        toc_html = '<div class="toc">\n  <h2>Table des matières</h2>\n  <ul>\n'

        for category, articles in grouped_articles.items():
            count = len(articles)
            category_id = self._slugify(category)
            toc_html += f'    <li><a href="#{category_id}">{category} ({count})</a></li>\n'

        toc_html += "  </ul>\n</div>\n"

        return toc_html

    def _generate_executive_summary_section(self, grouped_articles: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Generate executive summary section with all category summaries.

        Args:
            grouped_articles: Articles grouped by category

        Returns:
            HTML for executive summary section
        """
        if not grouped_articles:
            return ""

        summary_html = '<div class="executive-summary">\n'
        summary_html += '  <h2>📊 Résumés Exécutifs</h2>\n'

        for category, articles in grouped_articles.items():
            category_summary = self._generate_category_summary(articles)
            if category_summary:
                summary_html += '  <div class="summary-item">\n'
                summary_html += f'    <h4>{category}</h4>\n'
                summary_html += f'    <p>{category_summary}</p>\n'
                summary_html += '  </div>\n'

        summary_html += '</div>\n\n'

        return summary_html

    def _generate_category_section(self, category: str, articles: List[Dict[str, Any]]) -> str:
        """
        Generate HTML section for a category (details only, no summary).

        Args:
            category: Category name
            articles: List of articles in this category

        Returns:
            HTML for the category section
        """
        category_id = self._slugify(category)
        section_html = f'<section class="category" id="{category_id}">\n'
        section_html += f"  <h2>{category}</h2>\n"

        for article in articles:
            section_html += self._generate_article_html(article)

        section_html += "</section>\n\n"

        return section_html

    def _generate_article_html(self, article: Dict[str, Any]) -> str:
        """
        Generate HTML for a single article.

        Args:
            article: Article dictionary

        Returns:
            HTML for the article
        """
        title = self._escape_html(article.get("title", ""))
        link = self._escape_html(article.get("link", "#"))
        description = self._escape_html(article.get("description", ""))
        source = self._escape_html(article.get("source", ""))
        published = article.get("published", "")

        # Format date
        try:
            pub_date = datetime.fromisoformat(published)
            date_str = pub_date.strftime("%d/%m/%Y à %H:%M")
        except:
            date_str = "Date inconnue"

        article_html = f"""  <article class="article">
    <h3><a href="{link}" target="_blank">{title}</a></h3>
    <div class="article-meta">
      <span class="source">{source}</span>
      <span class="date">{date_str}</span>
    </div>
    <p class="description">{description}</p>
    <a href="{link}" class="read-more" target="_blank">Lire la suite →</a>
  </article>

"""

        return article_html

    def _generate_category_summary(self, articles: List[Dict[str, Any]]) -> str:
        """
        Generate an executive-friendly summary for a category.

        Combines key information from top articles using AI if translator is available.

        Args:
            articles: List of articles in the category

        Returns:
            Executive summary text
        """
        if not articles:
            return ""

        # Collect key information from top 3 articles
        article_info = []
        for article in articles[:3]:
            title = article.get("title", "").strip()
            description = article.get("description", "").strip()

            # Build article summary: title + description
            if title and description:
                # Get first 150 characters of description for context
                desc_excerpt = description[:150].strip()
                if len(description) > 150:
                    desc_excerpt += "..."
                article_info.append(f"{title}: {desc_excerpt}")
            elif title:
                article_info.append(title)
            elif description:
                article_info.append(description[:200])

        if not article_info:
            return ""

        # Create a comprehensive summary prompt
        articles_text = " | ".join(article_info)

        # If translator is available, use AI to generate executive summary
        if self.translator:
            try:
                summary_prompt = f"""Create a concise executive summary (2-3 sentences max) that captures the key trends and insights from these recent articles:

{articles_text}

Focus on business impact, trends, and actionable insights. Write for a C-level executive who needs quick understanding."""

                # Generate summary in English for better quality
                executive_summary = self.translator._translate_text_api(summary_prompt, "English")
                if executive_summary:
                    # Translate to target language if not English
                    if self.target_language != "English":
                        executive_summary = self.translator.translate_text(executive_summary, self.target_language)
                    return self._escape_html(executive_summary)
            except Exception as e:
                # Fall back to basic summary if AI generation fails
                pass

        # Fallback: Generate a simple summary from article titles
        titles = []
        for article in articles[:3]:
            title = article.get("title", "").strip()
            if title:
                titles.append(title)

        if titles:
            summary = "Key developments: " + " • ".join(titles[:2])
            return self._escape_html(summary[:300])

        return ""

    def _slugify(self, text: str) -> str:
        """
        Convert text to slug format.

        Args:
            text: Text to slugify

        Returns:
            Slugified text
        """
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        return text.strip("-")

    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
        }

        for char, escaped in replacements.items():
            text = text.replace(char, escaped)

        return text

    def summarize_article(self, article: Dict[str, Any]) -> str:
        """
        Generate a summary for an article.

        Args:
            article: Article dictionary

        Returns:
            Summary text (2-3 sentences max)
        """
        description = article.get("description", "")

        # If already short, return as is
        if len(description) <= 300:
            return description

        # Otherwise, truncate at sentence boundary
        sentences = re.split(r"(?<=[.!?])\s+", description)
        summary = ""
        word_count = 0

        for sentence in sentences:
            words = len(sentence.split())
            if word_count + words <= 60:  # Approximately 2-3 sentences
                summary += sentence + " "
                word_count += words
            else:
                break

        return summary.strip() + "..."
