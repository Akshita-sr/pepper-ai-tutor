# Pepper AI Tutor: RAG-Powered Interactive Puzzles

## 📖 Project Overview
This project turns a SoftBank Pepper robot into an intelligent, context-aware tutor. It uses **Retrieval Augmented Generation (RAG)** to allow the robot to "read" a PDF of puzzles and generate personalized hints for users using Large Language Models (LLMs) like Claude 3 or GPT-4.

## 🏗 Architecture
Because Pepper's NAOqi OS requires Python 2.7, but modern AI libraries require Python 3, this project uses a **Split-Process Architecture** connected via **ZeroMQ**.

1.  **The Brain (Python 3):** Handles logic, database, RAG (Vector Store), and LLM API calls.
2.  **The Body (Python 2.7):** A lightweight listener that translates JSON commands into NAOqi robot actions (Speech, Animation, Tablet).

## ✨ Features
*   **User Profiles:** Distinguishes between users (e.g., Kid vs. Adult) and adjusts the AI's personality accordingly.
*   **RAG Memory:** Ingests a PDF (`puzzles.pdf`) to create a searchable knowledge base.
*   **Smart Hints:** Generates dynamic hints using context from the PDF + the User's Persona.
*   **Analytics:** Logs which LLM models are used and how fast they respond.
*   **Model Routing:** Can switch between OpenAI, Anthropic, Google, or DeepSeek via config.

## 📂 Folder Structure
```text
pepper_ai_tutor/
├── main_brain_py3/           # THE BRAIN (Modern AI Logic)
│   ├── main_controller.py    # Main entry point for the logic
│   ├── setup_environment.py  # Run this ONCE to build the database/memory
│   ├── config.py             # API Keys and Robot IP
│   ├── services/             # Modules for DB, LLM, and RAG
│   └── data/                 # Source files (users.json, puzzles.pdf)
│
└── robot_listener_py27/      # THE BODY (Robot Interface)
    └── robot_listener.py     # Runs in a Python 2.7 env with NAOqi SDK





pepper_ai_tutor/
├── main_brain_py3/
│   ├── main_controller.py        # The master orchestrator (Python 3).
│   ├── setup_environment.py      # The one-time setup script (Python 3).
│   ├── config.py                 # Your API keys and robot IP.
│   ├── requirements.txt          # All Python 3 libraries.
│   │
│   ├── data/                     # Source data for setup.
│   │   ├── users.json            # User profiles (kid/adult).
│   │   └── puzzles.pdf           # Puzzles and hints for the RAG system.
│   │
│   ├── services/                 # The collection of "brain" modules.
│   │   ├── __init__.py
│   │   ├── robot_proxy.py        # Sends commands to the robot listener.
│   │   ├── database_manager.py     # Manages users, conversations, and analytics.
│   │   ├── llm_gateway.py          # Handles all API calls to different LLMs.
│   │   ├── document_processor.py   # Processes the puzzles.pdf for RAG.
│   │   ├── langchain_orchestrator.py # Builds prompts and uses RAG + LLMs.
│   │   └── analytics_manager.py    # Logs LLM usage to the database.
│   │
│   └── vector_store/
│       └── (This folder is created automatically by setup_environment.py)
│
└── robot_listener_py27/
    └── robot_listener.py         # The ONLY file that talks to the robot (Python 2.7).




+--------------------------------------------------------------------------------------------------+
|                                     THE AI BRAIN (Python 3)                                      |
|                                     (Client in our architecture)                                 |
+--------------------------------------------------------------------------------------------------+
| [main_controller.py]                                                                             |
|  - Knows current user is "Alex".                                                                 |
|  - Receives "hint" from RobotProxy.                                                              |
|  - DECIDES to get an AI-generated hint.                                                          |
|  - Calls orchestrator.generate_hint(puzzle, "hint", alex_profile)                                |
|          |                                                                                       |
|          v                                                                                       |
| [langchain_orchestrator.py] (The "Prompt Engineer" Middleman)                                    |
|  1. RECEIVES request for hint.                                                                   |
|  2. RAG - RETRIEVE: Searches 'vector_store' with "hint" + puzzle info --> finds "It's a breakfast food."|
|  3. RAG - AUGMENT: Builds a massive, detailed prompt:                                            |
|     "You are a cheerful tutor for 8-yr-old Alex... The puzzle is 'What breaks before use?'...      |
|      The user said 'hint'... The context I found is 'It's a breakfast food.'... Now, give a hint."|
|  4. Calls the LLMGateway with this rich prompt.                                                  |
|          |                                                                                       |
|          v                                                                                       |
| [llm_gateway.py] (The "API" Middleman)                                                           |
|  - Receives the rich prompt.                                                                     |
|  - Looks at `settings.LLM_FOR_HINTS` -> "claude-3-haiku...".                                      |
|  - Makes a specific API call to Anthropic's servers.                                             |
|  - Logs the call time via AnalyticsManager.                                                      |
|          |                                                                                       |
|          v                                                                                       |
+----------+---------------------------------------------------------------------------------------+
           |
           | Network API Call (HTTPS)
           v
+----------+--------------------+      +-------------------------+      +--------------------------+
| Anthropic/Claude Servers      |      | OpenAI/GPT Servers      |      | Google/Gemini Servers    |
+-------------------------------+      +-------------------------+      +--------------------------+
           ^
           | Network Communication (ZeroMQ on localhost:5555)
           |
+----------+---------------------------------------------------------------------------------------+
|                                  THE ROBOT CONTROLLER (Python 2.7)                               |
|                                     (Server in our architecture)                                 |
+--------------------------------------------------------------------------------------------------+
| [robot_listener.py]                                                                              |
|  - Listens for commands.                                                                         |
|  - Receives `{"action": "listen", ...}` command from RobotProxy.                                  |
|  - Uses NAOqi's speech recognition. Hears "hint".                                                |
|  - Sends `{"result": "hint"}` back to the RobotProxy.                                            |
|          ^                                                                                       |
|          | Physical Interaction (Speech, Tablet)                                                 |
|          v                                                                                       |
+----------+--------------------+                                                                  |
|   PEPPER ROBOT                | <---------------------> User ("Alex")                             |
+-------------------------------+                                                                  |
|  - Mic, Speaker, Tablet       |                                                                  |
|  - Runs NAOqi OS              |                                                                  |
+-------------------------------+------------------------------------------------------------------+

