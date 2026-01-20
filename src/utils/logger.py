"""Thread-safe logging utilities."""
import logging
import os
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
import contextvars


_cv_agent_id: contextvars.ContextVar[str] = contextvars.ContextVar('agent_id', default='N/A')
_cv_agent_name: contextvars.ContextVar[str] = contextvars.ContextVar('agent_name', default='N/A')


class AgentContextFilter(logging.Filter):
    """Injects agent context into log records."""
    
    def filter(self, record):
        record.agent_id = _cv_agent_id.get()
        record.agent_name = _cv_agent_name.get()
        return True


class SafeStreamHandler(logging.StreamHandler):
    """
    一个通过替换不兼容字符来处理UnicodeEncodeError的StreamHandler。
    适用于采用非UTF-8编码（例如GBK）的Windows控制台。
    """
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            try:
                stream.write(msg + self.terminator)
            except UnicodeEncodeError:
                # If the default encoding fails, try to print it safely
                # Get the encoding of the stream, default to utf-8 if None
                encoding = getattr(stream, 'encoding', 'utf-8') or 'utf-8'
                # Encode with replacement characters
                encoded_msg = msg.encode(encoding, errors='replace')
                # Decode back to string so stream.write accepts it
                decoded_msg = encoded_msg.decode(encoding)
                stream.write(decoded_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


class Logger:
    """Thread-safe singleton logger."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not Logger._initialized:
            self._setup_logger()
            Logger._initialized = True
    
    def _setup_logger(self, log_dir: Optional[str] = None, log_level: int = logging.INFO):
        """Configure the logging system."""
        self.logger = logging.getLogger('finsight')
        self.logger.setLevel(log_level)
        
        if self.logger.handlers:
            return
        
        detailed_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(agent_name)s:%(agent_id)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(agent_name)s:%(agent_id)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        context_filter = AgentContextFilter()
        
        # Use SafeStreamHandler instead of standard StreamHandler
        console_handler = SafeStreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        console_handler.addFilter(context_filter)
        self.logger.addHandler(console_handler)
        
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'finsight.log')
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(detailed_formatter)
            file_handler.addFilter(context_filter)
            self.logger.addHandler(file_handler)
    
    def set_log_dir(self, log_dir: str):
        """Configure the directory used for log files."""
        if not Logger._initialized:
            self._setup_logger(log_dir=log_dir)
        else:
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, 'finsight.log')
                detailed_formatter = logging.Formatter(
                    '%(asctime)s [%(levelname)s] [%(agent_name)s:%(agent_id)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                context_filter = AgentContextFilter()
                
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=10*1024*1024,
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(detailed_formatter)
                file_handler.addFilter(context_filter)
                
                has_file_handler = any(
                    isinstance(h, RotatingFileHandler) and h.baseFilename == log_file
                    for h in self.logger.handlers
                )
                if not has_file_handler:
                    self.logger.addHandler(file_handler)
    
    def set_agent_context(self, agent_id: str, agent_name: str):
        """Set the agent identifiers for the current async context."""
        _cv_agent_id.set(agent_id)
        _cv_agent_name.set(agent_name)
    
    def clear_agent_context(self):
        """Reset the agent identifiers for the current async context (restore to N/A)."""
        _cv_agent_id.set('N/A')
        _cv_agent_name.set('N/A')
    
    def debug(self, message: str, **kwargs):
        """Log a DEBUG-level message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log an INFO-level message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a WARNING-level message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log an ERROR-level message."""
        self.logger.error(message, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log an exception with stack trace."""
        self.logger.exception(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log a CRITICAL-level message."""
        self.logger.critical(message, **kwargs)
    
    def addHandler(self, handler):
        """Add a handler to the underlying logger."""
        self.logger.addHandler(handler)
    
    def removeHandler(self, handler):
        """Remove a handler from the underlying logger."""
        self.logger.removeHandler(handler)


# Global logger singleton
_logger_instance = None


def get_logger() -> Logger:
    """Return the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance


def setup_logger(log_dir: Optional[str] = None, log_level: int = logging.INFO) -> Logger:
    """Configure and return the logger instance."""
    logger = get_logger()
    logger._setup_logger(log_dir=log_dir, log_level=log_level)
    if log_dir:
        logger.set_log_dir(log_dir)
    return logger


# Convenience wrappers for the global logger
def debug(message: str, **kwargs):
    """Log a DEBUG-level message."""
    get_logger().debug(message, **kwargs)


def info(message: str, **kwargs):
    """Log an INFO-level message."""
    get_logger().info(message, **kwargs)


def warning(message: str, **kwargs):
    """Log a WARNING-level message."""
    get_logger().warning(message, **kwargs)


def error(message: str, exc_info: bool = False, **kwargs):
    """Log an ERROR-level message."""
    get_logger().error(message, exc_info=exc_info, **kwargs)


def exception(message: str, **kwargs):
    """Log an exception."""
    get_logger().exception(message, **kwargs)


def critical(message: str, **kwargs):
    """Log a CRITICAL-level message."""
    get_logger().critical(message, **kwargs)

