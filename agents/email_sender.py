"""
Email Sender Agent - Sends HTML emails with newsletter content via SMTP
"""

import logging
import smtplib
import os
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Any, Optional
from datetime import datetime


class EmailSender:
    """Sends emails with HTML content and optional attachments."""

    def __init__(self, logger: logging.Logger = None):
        """Initialize the Email Sender."""
        self.logger = logger
        self.status = "not_sent"
        self.message = ""
        self.template_dir = Path(__file__).parent.parent / "templates"

    def send_email(
        self,
        recipient: str,
        subject: str,
        html_content: str,
        email_config: Dict[str, Any],
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Send an HTML email.

        Args:
            recipient: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            email_config: Configuration with SMTP settings
            attachments: Optional list of file paths to attach

        Returns:
            Dict with 'status' and 'message'
        """
        try:
            # Extract SMTP configuration
            smtp_server = email_config.get("smtp_server")
            smtp_port = email_config.get("smtp_port")
            sender_email = email_config.get("sender_email")
            sender_password = email_config.get("sender_password")

            # Validate configuration
            if not all([smtp_server, smtp_port, sender_email, sender_password]):
                self.status = "error"
                self.message = "Missing email configuration"
                return {"status": self.status, "message": self.message}

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender_email
            message["To"] = recipient

            # Attach HTML content
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            # Attach files if provided
            if attachments:
                for attachment_path in attachments:
                    self._attach_file(message, attachment_path)

            # Send email via SMTP
            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)

            self.status = "success"
            self.message = f"Email sent successfully to {recipient}"
            return {"status": self.status, "message": self.message}

        except smtplib.SMTPAuthenticationError:
            self.status = "error"
            self.message = "SMTP authentication failed - check credentials"
            return {"status": self.status, "message": self.message}
        except smtplib.SMTPException as e:
            self.status = "error"
            self.message = f"SMTP error: {str(e)}"
            return {"status": self.status, "message": self.message}
        except Exception as e:
            self.status = "error"
            self.message = f"Error sending email: {str(e)}"
            return {"status": self.status, "message": self.message}

    def _load_template(self, filename: str) -> str:
        """
        Load a template file from the templates directory.

        Args:
            filename: Name of the template file

        Returns:
            Template content as string
        """
        template_path = self.template_dir / filename
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file not found: {template_path}")
        except Exception as e:
            raise Exception(f"Error loading template {filename}: {str(e)}")

    def _load_styles(self) -> str:
        """
        Load CSS styles from the styles template file.

        Returns:
            CSS content as string
        """
        return self._load_template("styles.css")

    def _attach_file(self, message: MIMEMultipart, file_path: str) -> None:
        """
        Attach a file to the email message.

        Args:
            message: Email message object
            file_path: Path to the file to attach
        """
        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(file_path)}",
            )
            message.attach(part)
        except Exception:
            pass  # Skip file if error

    def generate_newsletter_html(
        self,
        articles_html: str,
        stats: Dict[str, Any],
        include_date: bool = True,
    ) -> str:
        """
        Generate complete HTML email with header, footer, and content using templates.

        Args:
            articles_html: HTML content of articles
            stats: Statistics dict with counts and sources
            include_date: Whether to include current date

        Returns:
            Complete HTML email
        """
        try:
            # Load template and styles
            template = self._load_template("newsletter.html")
            styles = self._load_styles()

            # Prepare values
            today = datetime.now().strftime("%d %B %Y")
            generated_time = datetime.now().strftime("%d/%m/%Y à %H:%M")
            total_articles = stats.get("total_articles", 0)
            total_categories = stats.get("total_categories", 0)
            date_display = today if include_date else ""

            # Replace placeholders in template
            html = template.format(
                styles=styles,
                date=date_display,
                articles=articles_html,
                total_articles=total_articles,
                total_categories=total_categories,
                generated_time=generated_time,
            )

            return html

        except Exception as e:
            # Fallback to a minimal HTML if template loading fails
            return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Veille Technologique</title>
</head>
<body>
    <p>Erreur lors de la génération du template: {str(e)}</p>
    <div>{articles_html}</div>
</body>
</html>"""

    def send_error_email(
        self,
        recipient: str,
        agent_name: str,
        error_type: str,
        error_message: str,
        stack_trace: str,
        email_config: Dict[str, Any],
        log_attachment: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Send an error notification email using template.

        Args:
            recipient: Recipient email address
            agent_name: Name of the agent that failed
            error_type: Type of error
            error_message: Error message
            stack_trace: Full stack trace
            email_config: Email configuration
            log_attachment: Optional path to log file

        Returns:
            Dict with 'status' and 'message'
        """
        try:
            timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")

            # Load template and replace placeholders
            template = self._load_template("error_email.html")
            html_content = template.format(
                agent_name=self._escape_html(agent_name),
                error_type=self._escape_html(error_type),
                error_message=self._escape_html(error_message),
                stack_trace=self._escape_html(stack_trace),
                timestamp=timestamp,
            )

            subject = f"⚠️ Erreur Veille Tech - {timestamp}"

            attachments = []
            if log_attachment:
                attachments.append(log_attachment)

            return self.send_email(recipient, subject, html_content, email_config, attachments)

        except Exception as e:
            # Fallback to simple error response if template loading fails
            return {
                "status": "error",
                "message": f"Error sending error email: {str(e)}"
            }

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
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
