# main_brain_py3/settings.py
import logging

logger = logging.getLogger(__name__)

try:
    # This special import syntax allows us to treat config.py as a module
    # and access its variables directly.
    from config import ROBOT_LISTENER_IP, API_KEYS, LLM_FOR_HINTS, MAX_TOKENS_FOR_HINT
except ImportError:
    logger.critical("FATAL ERROR: config.py not found or is missing required variables.")
    logger.critical("Please create a config.py file from the template.")
    # In a real app, you might fall back to environment variables here.
    exit(1) # Exit immediately if config is missing.