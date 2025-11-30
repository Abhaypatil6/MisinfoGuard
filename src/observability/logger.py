import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict
import uuid

class StructuredLogger:
    """
    Structured JSON logger for observability
    Demonstrates: Observability - Logging concept
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        
        self.trace_id = None
    
    def set_trace_id(self, trace_id: str):
        """Set trace ID for request correlation"""
        self.trace_id = trace_id
    
    def _format_message(self, level: str, message: str, **kwargs) -> str:
        """Format log as JSON"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "logger": self.logger.name,
            "message": message,
            "trace_id": self.trace_id or "no-trace",
            **kwargs
        }
        return json.dumps(log_entry)
    
    def info(self, message: str, **kwargs):
        """Log info level message"""
        self.logger.info(self._format_message("INFO", message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error level message"""
        self.logger.error(self._format_message("ERROR", message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        self.logger.warning(self._format_message("WARNING", message, **kwargs))
    
    def debug(self, message: str, **kwargs):
        """Log debug level message"""
        self.logger.debug(self._format_message("DEBUG", message, **kwargs))

# Global logger registry
_loggers: Dict[str, StructuredLogger] = {}

def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger"""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]

def set_trace_id_for_all(trace_id: str):
    """Set trace ID for all loggers"""
    for logger in _loggers.values():
        logger.set_trace_id(trace_id)
