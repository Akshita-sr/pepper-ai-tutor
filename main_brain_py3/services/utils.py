# main_brain_py3/services/utils.py
import logging
import sys

def setup_logging():
    """
    Configures a standardized logger for the entire application.
    This ensures all modules produce logs in a consistent format.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(name)s.%(funcName)s:%(lineno)d] - %(message)s',
        stream=sys.stdout  # Log to the console
    )
    # Silence overly verbose libraries if needed
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)