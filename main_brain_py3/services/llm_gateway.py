#
# pepper_ai_tutor/main_brain_py3/services/llm_gateway.py (UPDATED)
#
# ==============================================================================
#  Purpose:
#  This module is the central hub for all interactions with external LLM APIs.
#  This updated version is "decoupled" - it has a single responsibility:
#  to call the requested LLM with a given prompt and return the text.
#  It no longer handles analytics logging itself; that is now the responsibility
#  of the calling function (the main_controller).
# ==============================================================================

import logging
import settings  # Imports configuration from your new settings.py file

# Import the specific client libraries for each LLM provider
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai

# Set up a logger for this module
logger = logging.getLogger(__name__)


class LLMGateway:
    """
    A simplified, focused gateway to interact with multiple LLM APIs.
    """

    def __init__(self):
        """
        Initializes the gateway by configuring all the necessary API clients
        using the centrally loaded settings.
        """
        logger.info("Initializing LLM Gateway clients...")

        # --- Configure OpenAI Client (for GPT models) ---
        self.openai_client = OpenAI(
            api_key=settings.API_KEYS.get("openai")
        )

        # --- Configure Anthropic Client (for Claude models) ---
        self.anthropic_client = Anthropic(
            api_key=settings.API_KEYS.get("anthropic")
        )

        # --- Configure Google Client (for Gemini models) ---
        try:
            genai.configure(api_key=settings.API_KEYS.get("google"))
            self.google_model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            logger.error(f"Failed to configure Google Gemini client: {e}")
            self.google_model = None

        # --- Configure DeepSeek Client ---
        self.deepseek_client = OpenAI(
            api_key=settings.API_KEYS.get("deepseek"),
            base_url="https://api.deepseek.com/v1"
        )

        logger.info("LLM Gateway initialized successfully.")

    def query(self, model_name: str, prompt: str, max_tokens: int) -> str:
        """
        Sends a prompt to the specified LLM and returns the response as a string.
        This method no longer logs analytics.

        Args:
            model_name (str): The specific model to use.
            prompt (str): The full prompt to send to the model.
            max_tokens (int): The maximum number of tokens for the response.

        Returns:
            str: The text content of the LLM's response.
        """
        logger.info(f"--- Sending query to model: {model_name} ---")
        response_text = ""

        try:
            # --- Model Routing Logic ---
            if "gpt" in model_name:
                response = self.openai_client.chat.completions.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.choices[0].message.content

            elif "claude" in model_name:
                response = self.anthropic_client.messages.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text

            elif "gemini" in model_name:
                if not self.google_model:
                    raise ConnectionError(
                        "Google Gemini client is not configured.")
                response = self.google_model.generate_content(prompt)
                response_text = response.text

            elif "deepseek" in model_name:
                response = self.deepseek_client.chat.completions.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.choices[0].message.content

            else:
                raise ValueError(
                    f"Unsupported or unknown model name: {model_name}")

        except Exception as e:
            logger.error(f"API call to model '{model_name}' failed: {e}")
            response_text = "I'm sorry, I'm having a little trouble thinking right now. Could you ask me again?"

        return response_text.strip()
