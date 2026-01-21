#
# pepper_ai_tutor/main_brain_py3/services/analytics_manager.py
#
# ==============================================================================
#  Purpose:
#  This module provides a dedicated service for logging performance and usage
#  analytics into the database. Its primary function is to record details
#  about each call made to an external Large Language Model (LLM) API.
#
#  By centralizing this functionality, we can easily track:
#    - Which LLMs are being used most often.
#    - The average response time for each model, which helps in identifying
#      fast or slow models.
#    - Usage patterns for different users.
#
#  This data is invaluable for optimizing the application's performance,
#  managing API costs, and understanding user engagement.
# ==============================================================================

import logging
import time

# This import is for "type hinting". It tells our code editor that this
# class expects to receive an object of type `DatabaseManager`.
from .database_manager import DatabaseManager

# Set up a logger for this module
logger = logging.getLogger(__name__)

class AnalyticsManager:
    """
    A service class to handle logging of usage analytics to the database.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initializes the AnalyticsManager. It doesn't create its own database
        connection; instead, it uses the one provided to it. This is more
        efficient as it prevents multiple, redundant connections to the database file.

        Args:
            db_manager (DatabaseManager): An active and initialized instance
                                          of the DatabaseManager service.
        """
        self.db_manager = db_manager
        logger.info("AnalyticsManager initialized.")

    def log_llm_call(self, user_id: int, model_name: str, response_time: float):
        """
        Logs a single LLM interaction event to the 'usage_analytics' table.
        This method is typically called from the LLMGateway immediately after
        an API call is completed.

        Args:
            user_id (int): The database ID of the user who triggered the LLM call.
                           This allows us to track usage per user.
            model_name (str): The name of the LLM that was used (e.g., "claude-3-haiku-20240307").
            response_time (float): The time in seconds it took to get the response
                                   from the moment the request was sent.
        """
        try:
            # The query to insert a new row into the analytics table.
            # We use placeholders (?) to prevent SQL injection vulnerabilities.
            query = "INSERT INTO usage_analytics (user_id, model_name, response_time) VALUES (?, ?, ?)"
            params = (user_id, model_name, response_time)
            
            self.db_manager.execute_query(query, params)
            
            # Log the action to the console for real-time monitoring.
            logger.info(f"Logged analytics: User ID={user_id}, Model='{model_name}', Response Time={response_time:.2f}s")
            
        except Exception as e:
            # If logging fails for any reason (e.g., database error), we don't want
            # it to crash the main application. We just log the error and move on.
            logger.error(f"Failed to log usage analytics for user {user_id}: {e}")