#
# config.py.template
#
# INSTRUCTIONS:
# 1. Copy this file and rename the copy to "config.py".
# 2. Fill in your actual Robot IP address and all your API keys in the new "config.py" file.
# 3. IMPORTANT: Never share your "config.py" file or commit it to a public repository like GitHub.
#

# --- Pepper Robot Configuration ---
ROBOT_IP = "10.186.13.49"  # <<< CHANGE THIS to your Pepper's actual IP address
ROBOT_PORT = 9559

# --- LLM API Keys ---
# Get your keys from the respective provider websites.
API_KEYS = {
    "openai": "INSERT_KEY_HERE",
    "google": "INSERT_KEY_HERE",
    "anthropic": "INSERT_KEY_HERE",
    "deepseek": "INSERT_KEY_HERE"
}

# --- OLLAMA Configuration ---
# The URL where your local Ollama instance is running.
OLLAMA_BASE_URL = "http://localhost:11434"