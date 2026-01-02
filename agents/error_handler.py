"""
Error Handler & Logger Agent - Captures errors and maintains detailed logs
"""

import os
import sys
import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler


class ErrorHandler:
    """Handles errors and logging throughout the system."""

    def __init__(self, log_dir: str = "logs", log_file: str = "veille_tech.log"):
        """
        Initialize the Error Handler.

        Args:
            log_dir: Directory for log files
            log_file: Name of the log file
        """
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, log_file)
        self.logger = self._setup_logger()
        self.errors: list = []

    def _setup_logger(self) -> logging.Logger:
        """
        Set up the logging configuration.

        Returns:
            Configured logger instance
        """
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)

        # Create logger
        logger = logging.getLogger("veille_tech")
        logger.setLevel(logging.DEBUG)

        # Console handler (INFO level)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%d/%m/%Y %H:%M:%S",
        )
        console_handler.setFormatter(console_format)

        # File handler (DEBUG level with rotation)
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
            datefmt="%d/%m/%Y %H:%M:%S",
        )
        file_handler.setFormatter(file_format)

        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    def log_info(self, message: str, agent: str = "SYSTEM") -> None:
        """
        Log an informational message.

        Args:
            message: Message to log
            agent: Name of the agent logging
        """
        self.logger.info(f"[{agent}] {message}")

    def log_warning(self, message: str, agent: str = "SYSTEM") -> None:
        """
        Log a warning message.

        Args:
            message: Message to log
            agent: Name of the agent logging
        """
        self.logger.warning(f"[{agent}] {message}")

    def log_error(self, message: str, agent: str = "SYSTEM") -> None:
        """
        Log an error message.

        Args:
            message: Message to log
            agent: Name of the agent logging
        """
        self.logger.error(f"[{agent}] {message}")

    def log_debug(self, message: str, agent: str = "SYSTEM") -> None:
        """
        Log a debug message.

        Args:
            message: Message to log
            agent: Name of the agent logging
        """
        self.logger.debug(f"[{agent}] {message}")

    def capture_error(
        self,
        agent: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Capture and log an error with context.

        Args:
            agent: Name of the agent where error occurred
            error_type: Type of error
            error_message: Error message
            context: Optional context dictionary

        Returns:
            Error record dictionary
        """
        # Get stack trace
        stack_trace = traceback.format_exc()

        # Create error record
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "type": error_type,
            "message": error_message,
            "stack_trace": stack_trace,
            "context": context or {},
        }

        # Log the error
        self.logger.error(
            f"[{agent}] {error_type}: {error_message}",
            exc_info=True,
        )

        # Store error record
        self.errors.append(error_record)

        return error_record

    def get_log_file_path(self) -> str:
        """
        Get the path to the log file.

        Returns:
            Path to the log file
        """
        return self.log_file

    def get_errors(self) -> list:
        """
        Get all captured errors.

        Returns:
            List of error records
        """
        return self.errors.copy()

    def get_last_error(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent error.

        Returns:
            Last error record or None
        """
        return self.errors[-1] if self.errors else None

    def clear_errors(self) -> None:
        """Clear the errors list."""
        self.errors = []

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current execution.

        Returns:
            Summary dictionary with statistics
        """
        return {
            "total_errors": len(self.errors),
            "log_file": self.log_file,
            "log_exists": os.path.exists(self.log_file),
            "errors": self.errors,
        }

    def format_error_for_email(self, error_record: Dict[str, Any]) -> str:
        """
        Format an error record for email notification.

        Args:
            error_record: Error record from capture_error

        Returns:
            Formatted error string
        """
        return f"""
Agent: {error_record.get('agent', 'Unknown')}
Type: {error_record.get('type', 'Unknown')}
Message: {error_record.get('message', 'No message')}
Timestamp: {error_record.get('timestamp', 'Unknown')}

Stack Trace:
{error_record.get('stack_trace', 'No stack trace')}

Context:
{self._format_dict(error_record.get('context', {}))}
"""

    def _format_dict(self, d: Dict[str, Any], indent: int = 0) -> str:
        """
        Format a dictionary for display.

        Args:
            d: Dictionary to format
            indent: Indentation level

        Returns:
            Formatted string
        """
        result = ""
        for key, value in d.items():
            if isinstance(value, dict):
                result += " " * indent + f"{key}:\n"
                result += self._format_dict(value, indent + 2)
            else:
                result += " " * indent + f"{key}: {value}\n"
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about errors logged.

        Returns:
            Statistics dictionary
        """
        error_types = {}
        agents_with_errors = {}

        for error in self.errors:
            error_type = error.get("type", "Unknown")
            agent = error.get("agent", "Unknown")

            error_types[error_type] = error_types.get(error_type, 0) + 1
            agents_with_errors[agent] = agents_with_errors.get(agent, 0) + 1

        return {
            "total_errors": len(self.errors),
            "error_types": error_types,
            "agents_with_errors": agents_with_errors,
            "log_file_path": self.log_file,
        }
