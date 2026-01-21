#
# pepper_ai_tutor/main_brain_py3/setup_environment.py (UPDATED)
#
# ==============================================================================
#  IMPORTANT: THIS SCRIPT SHOULD BE RUN ONCE BEFORE THE FIRST LAUNCH
# ==============================================================================
#
# Purpose:
# This script is a one-time utility to initialize the entire backend environment
# for the AI Tutor application. It prepares the database and the AI's knowledge
# base (the RAG vector store).
#
# It performs the following sequential tasks:
#   1. Sets up the standardized logging for clear console output.
#   2. Initializes the DatabaseManager and creates all necessary tables.
#   3. Reads the user profiles from `data/users.json` and securely adds them
#      to the `users` table in the database.
#   4. Reads the puzzle information from `data/puzzles.pdf` using the
#      DocumentProcessor.
#   5. Uses an embedding model (via OpenAI) to convert the puzzle text into
#      numerical vectors.
#   6. Creates and saves a FAISS vector store, which acts as the AI's
#      long-term, searchable memory for puzzle-related context.
#

import logging
import json
import sys

# --- Import Project-Specific Modules ---
# Import the new utility for standardized logging
from services.utils import setup_logging

# Import all the necessary service classes and the settings file
from services.database_manager import DatabaseManager
from services.document_processor import DocumentProcessor
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import settings

# --- Initial Setup ---
# Configure the logger as the very first step.
setup_logging()
logger = logging.getLogger(__name__)


def setup_environment():
    """
    Initializes the database, populates it with initial data, and creates
    the RAG vector store from source documents.
    """
    logger.info("==========================================================")
    logger.info("  STARTING AI TUTOR ENVIRONMENT SETUP SCRIPT  ")
    logger.info("==========================================================")

    # --- Step 1: Initialize the Database and Create Tables ---
    logger.info("STEP 1: Initializing database connection...")
    try:
        db = DatabaseManager()
        logger.info(
            "STEP 1: Setting up database tables (users, puzzles, analytics)...")
        db.setup_tables()
        logger.info("STEP 1: Database setup complete.")
    except Exception as e:
        logger.critical(
            f"Failed to set up the database. Error: {e}", exc_info=True)
        sys.exit(1)

    # --- Step 2: Populate Users from JSON Source File ---
    logger.info("----------------------------------------------------------")
    logger.info("STEP 2: Populating user profiles from 'data/users.json'...")
    try:
        with open('data/users.json', 'r') as f:
            users = json.load(f)
            if not users:
                logger.warning(
                    "data/users.json is empty. No users will be added.")
            for user in users:
                # Add each user to the database. The DatabaseManager handles hashing the PIN.
                db.add_user(user['username'], user['pin'], user['profile'])
                logger.info(f"  - Added user: {user['username']}")
        logger.info("STEP 2: User population complete.")
    except FileNotFoundError:
        logger.error(
            "Could not find 'data/users.json'. Skipping user population.")
    except Exception as e:
        logger.error(
            f"Failed to process 'data/users.json'. Error: {e}", exc_info=True)

    # --- Step 3: Create RAG Vector Store from Puzzle Source File ---
    logger.info("----------------------------------------------------------")
    logger.info("STEP 3: Processing puzzle source file for RAG system...")

    # You MUST create this PDF yourself and place it in the 'main_brain_py3/data/' folder.
    puzzle_source_file = 'data/puzzles.pdf'
    doc_processor = DocumentProcessor()

    try:
        # Use the DocumentProcessor to load and split the PDF into chunks.
        documents = doc_processor.process_pdf(puzzle_source_file)
        if not documents:
            raise ValueError(
                "Document processing resulted in zero chunks. Is the PDF empty?")
    except FileNotFoundError:
        logger.critical(
            f"FATAL: The puzzle source file '{puzzle_source_file}' was not found. The application cannot build the AI's memory.")
        sys.exit(1)
    except Exception as e:
        logger.critical(
            f"Failed to process '{puzzle_source_file}'. Error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("STEP 3: Creating AI vector store using OpenAI embeddings. This may take a moment and requires an internet connection...")
    try:
        # Use the OpenAI embedding model to convert text chunks into numerical vectors.
        embeddings = OpenAIEmbeddings(api_key=settings.API_KEYS["openai"])

        # Create the FAISS vector store from the documents and their embeddings.
        vector_store = FAISS.from_documents(documents, embeddings)

        # Save the completed vector store to a local folder for the main application to load.
        vector_store.save_local("vector_store")

        logger.info(
            "STEP 3: Vector store created and saved to 'vector_store' folder.")
    except Exception as e:
        logger.critical(
            f"Failed to create the vector store. Is your OpenAI API key valid? Error: {e}", exc_info=True)
        sys.exit(1)

    # --- Final Confirmation ---
    logger.info("----------------------------------------------------------")
    logger.info(
        "✅  Environment setup complete! You are now ready to run the main application.")
    logger.info("==========================================================")


if __name__ == "__main__":
    # This block ensures the setup_environment function is called only when
    # you execute the script directly (e.g., `python setup_environment.py`).
    setup_environment()
