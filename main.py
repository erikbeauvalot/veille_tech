#!/usr/bin/env python3
"""
Main orchestrator for the automated tech monitoring system.
Coordinates all agents to fetch, analyze, and send tech news.
"""

import sys
import time
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from agents import (
    ConfigManager,
    RSsFetcher,
    ContentAnalyzer,
    EmailSender,
    ErrorHandler,
    RSSDiscovery,
)


class VeilleTechOrchestrator:
    """Main orchestrator that coordinates all agents."""

    def __init__(self, config_path: str = "config.json", log_level: Optional[str] = None):
        """
        Initialize the orchestrator.

        Args:
            config_path: Path to configuration file
            log_level: Logging level override (ERROR, WARNING, INFO, DEBUG)
        """
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)

        # Determine effective log level
        if log_level is None:
            # Load config to get log_level
            config_result = self.config_manager.load_config()
            if config_result["status"] == "success":
                log_level = self.config_manager.get_log_level()
            else:
                log_level = "INFO"  # fallback

        # Create error handler with configured level
        self.error_handler = ErrorHandler(console_level=log_level)
        self.dry_run = False
        self.force = False

    def run(self, dry_run: bool = False, force: bool = False, days_ago: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the complete veille tech pipeline.

        Args:
            dry_run: If True, generate content but don't send email
            force: If True, ignore last execution date filter
            days_ago: If provided, filter articles from this ISO datetime (ignores last_execution)

        Returns:
            Execution result dictionary
        """
        # Track execution start time
        execution_start_time = datetime.now()

        self.dry_run = dry_run
        self.force = force

        self.error_handler.log_info("Starting veille tech execution", "ORCHESTRATOR")

        try:
            # Step 1: Load configuration
            self.error_handler.log_info("Loading configuration...", "ORCHESTRATOR")
            config_result = self.config_manager.load_config()
            if config_result["status"] != "success":
                return self._handle_fatal_error("CONFIG_MANAGER", config_result["message"])

            config = self.config_manager.get_config()
            rss_feeds = self.config_manager.get_rss_feeds()
            email_config = self.config_manager.get_email_config()
            discovery_config = self.config_manager.get_rss_discovery_config()

            # Step 2: Discover new RSS feeds
            if discovery_config.get("enabled", True):
                self.error_handler.log_info("Discovering new RSS feeds...", "ORCHESTRATOR")
                discovery = RSSDiscovery(logger=self.error_handler.logger)
                discovery_result = discovery.discover_feeds(
                    existing_feeds=rss_feeds,
                    max_new_feeds=discovery_config.get("max_new_feeds_per_run", 2),
                    validate=discovery_config.get("validate_feeds", True),
                )

                if discovery_result.get("discovered_feeds"):
                    self.error_handler.log_info(
                        f"Discovered {discovery_result['count']} new feeds",
                        "RSS_DISCOVERY",
                    )

                    # Auto-add new feeds if enabled
                    if discovery_config.get("auto_add_feeds", False):
                        for feed in discovery_result["discovered_feeds"]:
                            if self.config_manager.add_rss_feed(
                                feed["name"], feed["url"], feed["category"]
                            ):
                                self.error_handler.log_info(
                                    f"Added new feed: {feed['name']}",
                                    "RSS_DISCOVERY",
                                )
                                rss_feeds = self.config_manager.get_rss_feeds()
                        # Save updated config
                        self.config_manager.save_config()
                    else:
                        # Log discovered feeds for user review
                        self.error_handler.log_info(
                            "New feeds discovered but auto_add_feeds is disabled. "
                            "Review in logs and add manually if interested.",
                            "RSS_DISCOVERY",
                        )
                        for feed in discovery_result["discovered_feeds"]:
                            self.error_handler.log_info(
                                f"  - {feed['name']} ({feed['category']}): {feed['url']}",
                                "RSS_DISCOVERY",
                            )
                else:
                    self.error_handler.log_info(
                        "No new interesting feeds discovered",
                        "RSS_DISCOVERY",
                    )

            # Step 3: Fetch RSS feeds
            self.error_handler.log_info(f"Fetching {len(rss_feeds)} RSS feeds...", "ORCHESTRATOR")
            rss_fetcher = RSsFetcher(logger=self.error_handler.logger)
            fetch_result = rss_fetcher.fetch_feeds(rss_feeds)

            if fetch_result["status"] == "error":
                return self._handle_fatal_error("RSS_FETCHER", fetch_result["message"])

            articles = fetch_result["articles"]
            self.error_handler.log_info(
                f"Fetched {len(articles)} articles", "ORCHESTRATOR"
            )

            # Log any fetch errors
            if fetch_result.get("errors"):
                for error in fetch_result["errors"]:
                    self.error_handler.log_warning(
                        f"Feed error: {error.get('feed')} - {error.get('error')}",
                        "RSS_FETCHER",
                    )

            # Step 4: Filter articles by date if not forcing
            if not force:
                # Use --days parameter if provided, otherwise use last_execution
                if days_ago:
                    filter_date = days_ago
                    days_count = (datetime.now() - datetime.fromisoformat(days_ago)).days
                    self.error_handler.log_info(
                        f"Filtering articles from last {days_count} days",
                        "ORCHESTRATOR",
                    )
                else:
                    filter_date = self.config_manager.get_last_execution()

                if filter_date:
                    articles = rss_fetcher.filter_by_date(articles, filter_date)
                    self.error_handler.log_info(
                        f"Filtered to {len(articles)} new articles",
                        "ORCHESTRATOR",
                    )

            # Step 5: Limit articles per feed
            max_articles = self.config_manager.get_max_articles_per_feed()
            articles = rss_fetcher.limit_articles(articles, max_articles)
            self.error_handler.log_info(
                f"Limited to {len(articles)} articles per category",
                "ORCHESTRATOR",
            )

            # Check if there are any articles to send
            if len(articles) == 0:
                self.error_handler.log_info(
                    "No new articles found. Skipping email and updating last execution timestamp.",
                    "ORCHESTRATOR",
                )
                # Still update last execution time even if no articles
                self.config_manager.update_last_execution()
                language_preference = self.config_manager.get_language_preference()
                translation_provider = self.config_manager.get_translation_provider()
                translation_model = self.config_manager.get_model_for_provider(translation_provider)
                return {
                    "status": "success",
                    "message": "No new articles found - email not sent",
                    "execution_date": execution_start_time.isoformat(),
                    "articles_count": 0,
                    "categories_count": 0,
                    "language": language_preference,
                    "translation_provider": translation_provider,
                    "translation_model": translation_model,
                    "grouped_articles": {},
                    "exec_summaries": {},
                    "dry_run": self.dry_run,
                }

            # Step 6: Analyze and group content
            self.error_handler.log_info("Analyzing and grouping articles...", "ORCHESTRATOR")
            language_preference = self.config_manager.get_language_preference()
            translation_provider = self.config_manager.get_translation_provider()
            translation_model = self.config_manager.get_model_for_provider(translation_provider)
            self.error_handler.log_info(
                f"Translating articles to {language_preference} using {translation_provider} ({translation_model})",
                "ORCHESTRATOR",
            )
            content_analyzer = ContentAnalyzer(provider=translation_provider, model=translation_model, logger=self.error_handler.logger)
            analysis_result = content_analyzer.analyze_and_group(articles, target_language=language_preference)

            if analysis_result["status"] != "success":
                return self._handle_fatal_error("CONTENT_ANALYZER", analysis_result["message"])

            grouped_articles = analysis_result["grouped_articles"]

            # Step 6.5: Generate category summaries (before HTML generation)
            self.error_handler.log_info("Generating category summaries...", "ORCHESTRATOR")
            category_summaries = content_analyzer.generate_category_summaries(grouped_articles)

            # Step 7: Generate HTML
            self.error_handler.log_info("Generating HTML content...", "ORCHESTRATOR")
            articles_html = content_analyzer.generate_html(grouped_articles)

            # Step 8: Create complete email HTML
            email_sender = EmailSender(logger=self.error_handler.logger)
            stats = {
                "total_articles": analysis_result["total_articles"],
                "total_categories": analysis_result["total_categories"],
            }
            newsletter_html = email_sender.generate_newsletter_html(articles_html, stats)
            
            # Step 9: Send email (or dry-run)
            if self.dry_run:
                self.error_handler.log_info(
                    "DRY RUN MODE - Not sending email", "ORCHESTRATOR"
                )
                # Save HTML to file for inspection
                output_file = "newsletter_output.html"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(newsletter_html)
                self.error_handler.log_info(
                    f"Newsletter HTML saved to {output_file}",
                    "ORCHESTRATOR",
                )
            else:
                self.error_handler.log_info("Sending email...", "ORCHESTRATOR")
                recipient = email_config.get("recipient")
                subject = f"📰 Veille Technologique - {datetime.now().strftime('%d %B %Y à %H:%M')}"

                send_result = email_sender.send_email(
                    recipient=recipient,
                    subject=subject,
                    html_content=newsletter_html,
                    email_config=email_config,
                )

                if send_result["status"] != "success":
                    return self._handle_fatal_error("EMAIL_SENDER", send_result["message"])

                self.error_handler.log_info(
                    f"Email sent successfully to {recipient}",
                    "ORCHESTRATOR",
                )

            # Step 10: Update last execution time
            self.config_manager.update_last_execution()
            self.error_handler.log_info(
                "Updated last execution timestamp",
                "ORCHESTRATOR",
            )

            # Success
            self.error_handler.log_info("Execution completed successfully", "ORCHESTRATOR")

            return {
                "status": "success",
                "message": "Veille tech execution completed successfully",
                "execution_date": execution_start_time.isoformat(),
                "articles_count": len(articles),
                "categories_count": len(grouped_articles),
                "language": language_preference,
                "translation_provider": translation_provider,
                "translation_model": translation_model,
                "grouped_articles": grouped_articles,
                "exec_summaries": category_summaries,
                "dry_run": self.dry_run,
            }

        except Exception as e:
            return self._handle_fatal_error("ORCHESTRATOR", str(e))

    def _handle_fatal_error(self, agent: str, error_message: str) -> Dict[str, Any]:
        """
        Handle a fatal error and attempt to send error notification.

        Args:
            agent: Name of the agent that failed
            error_message: Error message

        Returns:
            Error result dictionary
        """
        import traceback

        # Log the error
        error_record = self.error_handler.capture_error(
            agent=agent,
            error_type="Fatal Error",
            error_message=error_message,
        )

        self.error_handler.log_error(
            f"Fatal error in {agent}: {error_message}",
            "ORCHESTRATOR",
        )

        # Try to send error notification email (if not in dry-run)
        if not self.dry_run:
            try:
                config_result = self.config_manager.load_config()
                if config_result["status"] == "success":
                    email_config = self.config_manager.get_email_config()
                    recipient = email_config.get("recipient")

                    email_sender = EmailSender()
                    email_sender.send_error_email(
                        recipient=recipient,
                        agent_name=agent,
                        error_type="Fatal Error",
                        error_message=error_message,
                        stack_trace=traceback.format_exc(),
                        email_config=email_config,
                        log_attachment=self.error_handler.get_log_file_path(),
                    )

                    self.error_handler.log_info(
                        f"Error notification email sent to {recipient}",
                        "ORCHESTRATOR",
                    )
            except Exception as email_error:
                self.error_handler.log_error(
                    f"Failed to send error notification: {str(email_error)}",
                    "ORCHESTRATOR",
                )

        return {
            "status": "error",
            "message": error_message,
            "execution_date": datetime.now().isoformat(),
            "articles_count": 0,
            "categories_count": 0,
            "agent": agent,
            "log_file": self.error_handler.get_log_file_path(),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated tech monitoring system"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate newsletter without sending email",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore last execution date filter",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file (default: config.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    parser.add_argument(
        "--log-level",
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        help="Set logging level (overrides config.json)",
    )
    parser.add_argument(
        "--days",
        type=int,
        metavar="N",
        help="Filter articles from last N days (ignores last_execution)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of plain text",
    )

    args = parser.parse_args()

    # Determine effective log level (CLI > config > default)
    log_level = None
    if args.verbose:
        log_level = "DEBUG"
    elif args.log_level:
        log_level = args.log_level

    # Calculate date filter if --days provided
    days_ago = None
    if args.days:
        days_ago = (datetime.now() - timedelta(days=args.days)).isoformat()

    # Run orchestrator
    orchestrator = VeilleTechOrchestrator(config_path=args.config, log_level=log_level)
    result = orchestrator.run(dry_run=args.dry_run, force=args.force, days_ago=days_ago)

    # Output results
    if args.json:
        # JSON output mode
        json_output = {
            "metadata": {
                "execution_date": result.get("execution_date", datetime.now().isoformat()),
                "status": result["status"],
                "message": result["message"],
                "articles_count": result.get("articles_count", 0),
                "categories_count": result.get("categories_count", 0),
                "language": result.get("language", "N/A"),
                "translation_provider": result.get("translation_provider", "N/A"),
                "translation_model": result.get("translation_model", "N/A"),
            },
            "exec_summary": result.get("exec_summaries", {}),
            "details": result.get("grouped_articles", {})
        }

        # Output to stdout
        json_str = json.dumps(json_output, indent=2, ensure_ascii=False)
        print(json_str)

        # Save to file
        output_file = "veille_tech_output.json"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"\n✓ JSON output saved to {output_file}", file=sys.stderr)
        except Exception as e:
            print(f"\n✗ Failed to save JSON to {output_file}: {str(e)}", file=sys.stderr)
    else:
        # Original text output mode
        print("\n" + "=" * 50)
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        if result["status"] == "success":
            print(f"Articles: {result.get('articles_count', 0)}")
            print(f"Categories: {result.get('categories_count', 0)}")
        if result["status"] == "error":
            print(f"Log file: {result.get('log_file', 'N/A')}")
        print("=" * 50 + "\n")

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
