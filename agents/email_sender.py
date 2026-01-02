"""
Email Sender Agent - Sends HTML emails with newsletter content via SMTP
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Any, Optional
from datetime import datetime


class EmailSender:
    """Sends emails with HTML content and optional attachments."""

    def __init__(self):
        """Initialize the Email Sender."""
        self.status = "not_sent"
        self.message = ""

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
        Generate complete HTML email with header, footer, and content.

        Args:
            articles_html: HTML content of articles
            stats: Statistics dict with counts and sources
            include_date: Whether to include current date

        Returns:
            Complete HTML email
        """
        today = datetime.now().strftime("%d %B %Y")
        total_articles = stats.get("total_articles", 0)
        total_categories = stats.get("total_categories", 0)

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Veille Technologique</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}

        .header .date {{
            font-size: 14px;
            opacity: 0.9;
        }}

        .content {{
            padding: 30px 20px;
        }}

        .toc {{
            background-color: #f9f9f9;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 4px;
        }}

        .toc h2 {{
            font-size: 16px;
            margin-bottom: 15px;
            color: #667eea;
        }}

        .toc ul {{
            list-style: none;
            padding-left: 0;
        }}

        .toc li {{
            margin-bottom: 8px;
        }}

        .toc a {{
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
        }}

        .toc a:hover {{
            text-decoration: underline;
        }}

        .category {{
            margin-bottom: 40px;
        }}

        .category h2 {{
            font-size: 22px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}

        .category-summary {{
            background-color: #e8eef9;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}

        .category-summary h3 {{
            font-size: 14px;
            color: #667eea;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .category-summary p {{
            font-size: 13px;
            color: #555;
            line-height: 1.5;
        }}

        .article {{
            margin-bottom: 25px;
            padding: 15px;
            background-color: #fafafa;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }}

        .article h3 {{
            font-size: 16px;
            margin-bottom: 10px;
        }}

        .article h3 a {{
            color: #667eea;
            text-decoration: none;
        }}

        .article h3 a:hover {{
            text-decoration: underline;
        }}

        .article-meta {{
            font-size: 12px;
            color: #999;
            margin-bottom: 10px;
            display: flex;
            gap: 15px;
        }}

        .source {{
            font-weight: 500;
            color: #667eea;
        }}

        .description {{
            font-size: 14px;
            color: #555;
            margin-bottom: 10px;
            line-height: 1.5;
        }}

        .read-more {{
            display: inline-block;
            color: #667eea;
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
        }}

        .read-more:hover {{
            text-decoration: underline;
        }}

        .footer {{
            background-color: #f9f9f9;
            border-top: 1px solid #e0e0e0;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #999;
        }}

        .stats {{
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-bottom: 15px;
            font-size: 13px;
        }}

        .stat {{
            background-color: white;
            padding: 10px 15px;
            border-radius: 4px;
            border: 1px solid #e0e0e0;
        }}

        .stat-value {{
            font-weight: bold;
            color: #667eea;
            font-size: 16px;
        }}

        @media (max-width: 600px) {{
            .header {{
                padding: 30px 15px;
            }}

            .header h1 {{
                font-size: 24px;
            }}

            .content {{
                padding: 20px 15px;
            }}

            .article {{
                padding: 12px;
            }}

            .article h3 {{
                font-size: 15px;
            }}

            .category-summary {{
                padding: 12px;
            }}

            .category-summary h3 {{
                font-size: 12px;
            }}

            .stats {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 Veille Technologique</h1>
            <div class="date">{today if include_date else ''}</div>
        </div>

        <div class="content">
            {articles_html}
        </div>

        <div class="footer">
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{total_articles}</div>
                    <div>articles</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{total_categories}</div>
                    <div>catégories</div>
                </div>
            </div>
            <p>Veille technologique automatisée</p>
            <p style="margin-top: 10px;">Générée le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
        </div>
    </div>
</body>
</html>"""

        return html

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
        Send an error notification email.

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
        timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")

        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erreur Veille Tech</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .header {{
            background-color: #dc3545;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .content {{
            padding: 20px;
        }}
        .details {{
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        .details dt {{
            font-weight: bold;
            color: #333;
            margin-top: 10px;
        }}
        .details dd {{
            margin-left: 0;
            color: #666;
            margin-bottom: 10px;
        }}
        .stacktrace {{
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
            margin-bottom: 20px;
        }}
        .footer {{
            text-align: center;
            padding: 10px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Erreur Veille Technologique</h1>
        </div>
        <div class="content">
            <p>Bonjour,</p>
            <p>Une erreur s'est produite lors de l'exécution de la veille technologique.</p>

            <div class="details">
                <dl>
                    <dt>Agent:</dt>
                    <dd>{agent_name}</dd>
                    <dt>Type d'erreur:</dt>
                    <dd>{error_type}</dd>
                    <dt>Message:</dt>
                    <dd>{error_message}</dd>
                    <dt>Timestamp:</dt>
                    <dd>{timestamp}</dd>
                </dl>
            </div>

            <h3>Stack Trace:</h3>
            <div class="stacktrace">{self._escape_html(stack_trace)}</div>

            <p>Veuillez consulter les logs en pièce jointe pour plus de détails.</p>
        </div>
        <div class="footer">
            <p>Email généré automatiquement par le système de veille</p>
        </div>
    </div>
</body>
</html>"""

        subject = f"⚠️ Erreur Veille Tech - {timestamp}"

        attachments = []
        if log_attachment:
            attachments.append(log_attachment)

        return self.send_email(recipient, subject, html_content, email_config, attachments)

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
