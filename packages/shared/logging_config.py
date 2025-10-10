"""Centralized logging configuration for production-grade logging."""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add log level
        log_record['severity'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add source location
        log_record['source_location'] = {
            'file': record.pathname,
            'line': record.lineno,
            'function': record.funcName
        }


def setup_logging(service_name: str, log_level: str = "INFO", structured: bool = True) -> logging.Logger:
    """
    Set up logging configuration for a service.
    
    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Whether to use structured (JSON) logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    if structured:
        # Use JSON formatter for production
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(severity)s %(logger)s %(message)s'
        )
    else:
        # Use standard formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

