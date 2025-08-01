"""
Logging Configuration
Provides consistent logging setup across all agents
"""

import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry)

def setup_logging(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = True,
    config: Optional[Dict[str, Any]] = None
) -> logging.Logger:
    """Setup logging for an agent or component"""
    
    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add custom methods for structured logging
    def log_with_context(self, level: str, message: str, **kwargs):
        """Log with additional context"""
        record = logging.LogRecord(
            name=self.name,
            level=getattr(logging, level.upper()),
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_fields = kwargs
        self.handle(record)
    
    # Attach custom method to logger
    logger.log_with_context = lambda level, message, **kwargs: log_with_context(logger, level, message, **kwargs)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

class AgentLogger:
    """Specialized logger for agents with additional context"""
    
    def __init__(self, agent_name: str, config: Optional[Dict[str, Any]] = None):
        self.agent_name = agent_name
        self.logger = setup_logging(
            f"agent.{agent_name}",
            level=config.get("logging", {}).get("level", "INFO") if config else "INFO",
            log_file=f"logs/{agent_name}.log" if config else None,
            structured=True
        )
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.log_with_context("INFO", message, agent=self.agent_name, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.log_with_context("WARNING", message, agent=self.agent_name, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.log_with_context("ERROR", message, agent=self.agent_name, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.log_with_context("DEBUG", message, agent=self.agent_name, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context"""
        self.logger.log_with_context("CRITICAL", message, agent=self.agent_name, **kwargs)

class ToolLogger:
    """Specialized logger for tools"""
    
    def __init__(self, tool_name: str, agent_name: str):
        self.tool_name = tool_name
        self.agent_name = agent_name
        self.logger = setup_logging(
            f"tool.{agent_name}.{tool_name}",
            structured=True
        )
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.log_with_context("INFO", message, tool=self.tool_name, agent=self.agent_name, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.log_with_context("WARNING", message, tool=self.tool_name, agent=self.agent_name, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.log_with_context("ERROR", message, tool=self.tool_name, agent=self.agent_name, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.log_with_context("DEBUG", message, tool=self.tool_name, agent=self.agent_name, **kwargs)
