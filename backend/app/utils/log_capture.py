import logging
from typing import List, Dict
from datetime import datetime
from contextlib import contextmanager


class LogCaptureHandler(logging.Handler):
    """Custom handler to capture log records in memory"""
    
    def __init__(self):
        super().__init__()
        self.logs: List[Dict] = []
    
    def emit(self, record: logging.LogRecord):
        """Capture log record"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": self.format(record)
            }
            self.logs.append(log_entry)
        except Exception:
            self.handleError(record)
    
    def get_logs(self) -> List[Dict]:
        """Get captured logs as list of dicts"""
        return self.logs
    
    def get_logs_as_string(self) -> str:
        """Get captured logs as a single formatted string"""
        return "\n".join([log["message"] for log in self.logs])
    
    def clear(self):
        """Clear captured logs"""
        self.logs = []


@contextmanager
def capture_logs(logger_name: str = "abbotsford"):
    """
    Context manager to capture logs during execution
    
    Usage:
        with capture_logs() as log_capture:
            # Your code here
            logger.info("Something happened")
        
        logs = log_capture.get_logs()
    """
    logger = logging.getLogger(logger_name)
    handler = LogCaptureHandler()
    
    # Use same formatter as main logger
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add handler
    logger.addHandler(handler)
    
    try:
        yield handler
    finally:
        # Remove handler
        logger.removeHandler(handler)
