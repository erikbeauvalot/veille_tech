"""
Content Analyzer & Summarizer Agent - Groups articles and generates HTML summary
"""

from typing import List, Dict, Any
from datetime import datetime
import re
from .translator import Translator


class ContentAnalyzer:
    """Analyzes content and groups articles by category."""

    def __init__(self, provider: str = "Claude", model: str = None):
        """
        Initialize the Content Analyzer.

        Args:
            provider: Translation provider ("Claude" or "OpenAI")
            model: Model to use (optional, uses defaults if not specified)
        """
        self.grouped_articles: Dict[str, List[Dict[str, Any]]] = {}
        self.status = "not_analyzed"
        self.message = ""
        self.translation_provider = provider
        self.translation_model = model
        try:
            self.translator = Translator.create(provider, model=model)
        except ValueError as e:
            # If API key not set or invalid provider, translator will be None
            self.translator = None
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

    def generate_html(self, grouped_articles: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Generate HTML summary from grouped articles.

        Args:
            grouped_articles: Articles grouped by category

        Returns:
            HTML string
        """
        html_content = ""

        # Generate table of contents
        html_content += self._generate_toc(grouped_articles)

        # Generate sections for each category with summaries
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

    def _generate_category_section(self, category: str, articles: List[Dict[str, Any]]) -> str:
        """
        Generate HTML section for a category.

        Args:
            category: Category name
            articles: List of articles in this category

        Returns:
            HTML for the category section
        """
        category_id = self._slugify(category)
        section_html = f'<section class="category" id="{category_id}">\n'
        section_html += f"  <h2>{category}</h2>\n"

        # Generate category summary
        category_summary = self._generate_category_summary(articles)
        if category_summary:
            section_html += f'  <div class="category-summary">\n'
            section_html += f'    <h3>Résumé de la catégorie</h3>\n'
            section_html += f'    <p>{category_summary}</p>\n'
            section_html += f'  </div>\n\n'

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
        Generate a summary for a category by combining key points from all articles.

        Args:
            articles: List of articles in the category

        Returns:
            Summary text
        """
        if not articles:
            return ""

        # Extract and combine summaries from top 3 articles
        summaries = []
        for article in articles[:3]:
            description = article.get("description", "").strip()
            if description:
                # Limit each summary to ~100 characters
                summary = description[:100].strip()
                if len(description) > 100:
                    summary += "..."
                summaries.append(summary)

        if not summaries:
            return ""

        # Combine summaries with bullet points
        combined = " ".join(summaries)

        # Escape HTML characters
        combined = self._escape_html(combined)

        # Return as a single paragraph
        return combined

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
