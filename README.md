# Pepper AI Tutor: RAG-Powered Interactive Puzzles

## 📖 Project Overview

This project turns a SoftBank Pepper robot into an intelligent, context-aware tutor. It uses **Retrieval Augmented Generation (RAG)** to allow the robot to "read" a PDF of puzzles and generate personalized hints for users using Large Language Models (LLMs) like Claude 3 or GPT-4.

## 🏗 Architecture

Because Pepper's NAOqi OS requires Python 2.7, but modern AI libraries require Python 3, this project uses a **Split-Process Architecture** connected via **ZeroMQ**.

1. **The Brain (Python 3):** Handles logic, database, RAG (Vector Store), and LLM API calls.
2. **The Body (Python 2.7):** A lightweight listener that translates JSON commands into NAOqi robot actions (Speech, Animation, Tablet).

## ✨ Features

* **User Profiles:** Distinguishes between users (e.g., Kid vs. Adult) and adjusts the AI's personality accordingly.
* **RAG Memory:** Ingests a PDF (`puzzles.pdf`) to create a searchable knowledge base.
* **Smart Hints:** Generates dynamic hints using context from the PDF + the User's Persona.
* **Analytics:** Logs which LLM models are used and how fast they respond.
* **Model Routing:** Can switch between OpenAI, Anthropic, Google, or DeepSeek via config.

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



I can see the issue - you're encountering a Python 2.7 virtual environment creation problem due to incompatibilities between modern `virtualenv` versions and Python 2.7. Let me provide you with a **complete, step-by-step guide** to get this working.

## The Problem

Your Python 2.7 installation is having issues with modern `virtualenv`. Since you're working with **Choregraphe simulation** (based on your second robot_listener.py file), we can simplify this significantly.

## Solution: Step-by-Step Guide

### Phase 1: Set Up Python 2.7 Environment (For Robot Listener)

Since virtualenv is problematic with Python 2.7, let's use the **simpler approach** - install dependencies directly into your Python 2.7 installation:

```cmd
REM Step 1: Install ZeroMQ for Python 2.7
C:\Python27\python.exe -m pip install pyzmq

REM Step 2: Verify installation
C:\Python27\python.exe -c "import zmq; print('ZeroMQ installed successfully')"
```

### Phase 2: Configure Choregraphe

1. **Open Choregraphe**
2. **Start the Virtual Robot** (it should appear automatically)
3. **Find the Port Number:**
   - Look at the top menu: `Connection` → `Connect to...`
   - You'll see something like: `127.0.0.1:54321` (the number after the colon is your port)
   - **Write this port number down** - you'll need it in the next step

### Phase 3: Update Robot Listener Configuration

Open `robot_listener_py27/robot_listener.py` and update these lines:

```python
# Around line 20-25, change this:
ROBOT_IP = "127.0.0.1"
ROBOT_PORT = 12345  # <--- CHANGE THIS TO YOUR CHOREGRAPHE PORT (e.g., 54321)
```

### Phase 4: Verify Your Python 3 Environment is Ready

```cmd
REM Make sure you're in your Python 3 venv
C:\Users\akshi\OneDrive\Desktop\pepper_llm_final\venv_brain\Scripts\activate.bat

REM Verify your environment setup was successful (you already did this!)
cd main_brain_py3
dir vector_store
REM You should see files in the vector_store folder
```

### Phase 5: Launch the System

**Terminal 1 - Start the Robot Listener (Python 2.7):**

```cmd
REM Open a NEW Command Prompt window
cd C:\Users\akshi\OneDrive\Desktop\pepper_llm_final\robot_listener_py27

REM Run with Python 2.7 directly (no virtual environment needed)
C:\Python27\python.exe robot_listener.py
```

**Expected Output:**
```
--------------------------------------------------
   ROBOT LISTENER (PYTHON 2.7) - SIMULATION MODE  
--------------------------------------------------
Connecting to Choregraphe at 127.0.0.1:54321...
[Robot Listener] NAOqi service proxies are ready.
Connected to brain.
[ZeroMQ] Server started on port 5555.
[ZeroMQ] Waiting for commands from Python 3 Brain...
```

**Terminal 2 - Start the AI Brain (Python 3):**

```cmd
REM Open a SECOND Command Prompt window
cd C:\Users\akshi\OneDrive\Desktop\pepper_llm_final

REM Activate your Python 3 virtual environment
venv_brain\Scripts\activate.bat

REM Navigate to the brain folder
cd main_brain_py3

REM Run the main controller
python main_controller.py
```

### Phase 6: Interact with the System

Once both terminals are running:

1. The virtual Pepper in Choregraphe will say: **"Hello, please say your username to begin."**
2. In **Terminal 1** (Python 2.7), you'll see a prompt asking you to type your username
3. Type: `Alex` and press Enter
4. Type: (when asked for puzzle answer or hint) `hint` and press Enter
5. The AI will generate a personalized hint using RAG + LLM!

## Troubleshooting Common Issues

### Issue 1: "Could not connect to Choregraphe"
**Solution:** 
- Verify Choregraphe is running with the virtual robot active
- Double-check the port number in `robot_listener.py` matches Choregraphe

### Issue 2: "ModuleNotFoundError: No module named 'qi'"
**Solution:**
You need the NAOqi SDK. Download it from:
- SoftBank Robotics website (requires registration)
- Or add the Choregraphe SDK to your PYTHONPATH:

```cmd
REM Windows Command:
set PYTHONPATH=C:\Program Files (x86)\Softbank Robotics\Choregraphe Suite 2.5\lib;%PYTHONPATH%

REM Then run the robot listener
C:\Python27\python.exe robot_listener.py
```

### Issue 3: "No response from robot listener"
**Solution:**
- Make sure Terminal 1 (robot_listener.py) is running and shows "Waiting for commands..."
- Check that both scripts are using the same port (5555 by default)

## Quick Verification Checklist

Before running, verify:

- ✅ Choregraphe is open with virtual robot running
- ✅ `robot_listener.py` has the correct port number from Choregraphe
- ✅ `main_brain_py3/config.py` has your OpenAI/Anthropic API keys
- ✅ `main_brain_py3/vector_store/` folder exists and has files in it
- ✅ Python 2.7 has `pyzmq` installed: `C:\Python27\python.exe -m pip install pyzmq`
- ✅ Python 3 venv is activated and has all dependencies

## Alternative: Test Connection First

Before running the full system, test the connection:

**Terminal 1:**
```cmd
cd robot_listener_py27
C:\Python27\python.exe robot_listener.py
```

**Terminal 2:**
```cmd
cd main_brain_py3
python
>>> from services.robot_proxy import RobotProxy
>>> robot = RobotProxy("localhost", 5555)
>>> robot.ping()
True  # <-- If you see this, connection works!
>>> robot.say("Hello, I am testing!")  # Choregraphe robot should speak
>>> exit()
```

If the test works, proceed to run the full `main_controller.py`!

Let me know which error you encounter at any step, and I'll help you resolve it!