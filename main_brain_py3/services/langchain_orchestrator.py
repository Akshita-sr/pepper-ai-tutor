#
# pepper_ai_tutor/main_brain_py3/services/langchain_orchestrator.py (UPDATED)
#
# ==============================================================================
#  Purpose:
#  This module is the core of the "thinking" process. It uses the LangChain
#  framework to perform Retrieval-Augmented Generation (RAG).
#
#  Its workflow is:
#  1. Receive the puzzle, the user's specific input, and the user's profile.
#  2. Use the user's input to "retrieve" the most relevant information (hints,
#     solutions, etc.) from the pre-built vector store (the AI's memory).
#  3. "Augment" a detailed prompt template with all of this context: the user's
#     persona, the puzzle question, and the retrieved information.
#  4. Pass this final, rich prompt to the LLMGateway for "generation".
#
#  This process ensures the hints are not generic, but are contextually
#  relevant to the puzzle and tailored to the specific user's learning style.
# ==============================================================================

import logging
import settings  # Imports configuration from your new settings.py file

# --- LangChain Core Imports ---
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# --- Project-Specific Imports ---
from .llm_gateway import LLMGateway

# Set up a logger for this module
logger = logging.getLogger(__name__)


class LangChainOrchestrator:
    """
    Orchestrates the RAG process to generate context-aware and personalized hints.
    """

    def __init__(self, llm_gateway: LLMGateway):
        """
        Initializes the orchestrator by loading the vector store and setting up the retriever.

        Args:
            llm_gateway (LLMGateway): An initialized instance of the LLMGateway.
        """
        self.llm_gateway = llm_gateway

        try:
            logger.info("Initializing LangChain Orchestrator...")
            # Use OpenAI embeddings, which are reliable and a standard choice for RAG.
            # This must match the embeddings used in the setup_environment.py script.
            embeddings = OpenAIEmbeddings(api_key=settings.API_KEYS["openai"])

            # Load the pre-built FAISS vector store from the local directory.
            vector_store = FAISS.load_local(
                "vector_store", embeddings, allow_dangerous_deserialization=True)

            # Create a "retriever" from the vector store. The retriever is an object
            # that can efficiently search for the most relevant documents.
            self.retriever = vector_store.as_retriever()

            logger.info(
                "LangChain Orchestrator: FAISS vector store loaded successfully.")

        except Exception as e:
            logger.critical(
                f"FATAL: Failed to load vector store. Did you run setup_environment.py successfully? Error: {e}", exc_info=True)
            # This is a critical error; the application cannot function without the vector store.
            raise

    def generate_hint(self, puzzle: dict, user_input: str, user_profile: dict) -> str:
        """
        Generates a personalized hint using the full RAG pipeline.

        Args:
            puzzle (dict): A dictionary containing details about the current puzzle.
            user_input (str): The specific word or phrase the user said.
            user_profile (dict): A dictionary containing the user's persona and details.

        Returns:
            str: The AI-generated hint.
        """
        logger.info(
            f"Generating hint for user '{user_profile.get('name')}' on puzzle '{puzzle.get('puzzle_id')}'")

        # This is the master prompt template. It contains placeholders for all the
        # dynamic information we will provide. This is the heart of "prompt engineering."
        template = """
        You are Pepper, a helpful and friendly robot tutor. Your personality MUST adapt to the user you are talking to.
        
        **Your Current User's Profile:**
        Your current user is {user_name}, aged {user_age}. You must speak to them as if you are {user_persona}.

        **The Current Puzzle:**
        The user is trying to solve this riddle: "{puzzle_question}"

        **Retrieved Context from Memory:**
        Based on the user's input, here is the most relevant information I found about this puzzle in my memory banks:
        ---
        {context}
        ---

        **The User's Recent Input:**
        The user just said: "{user_input}"

        **Your Task:**
        Based on ALL of the information above, your goal is to provide a single, short, and helpful hint.
        - **Adhere to the User's Persona:** Your tone and style must match the user's profile.
        - **Do NOT give away the final answer.** Guide them, don't solve it for them.
        - **Be Concise:** Keep your response to 1-3 sentences.
        - **Be Conversational:** Phrase your response as if you are speaking directly to the user.
        """

        prompt_template = ChatPromptTemplate.from_template(template)

        # This chain defines the sequence of operations for the RAG process.
        # It's read from top to bottom.
        rag_chain = (
            {
                # The 'context' is filled by running the user's input through our retriever.
                "context": self.retriever,
                # 'user_input' is passed through directly from the input.
                "user_input": RunnablePassthrough(),
            }
            # The retrieved context and user input are fed into our prompt template.
            | prompt_template
            # The filled prompt is sent to our LLM gateway.
            | (lambda p: self.llm_gateway.query(settings.LLM_FOR_HINTS, p.to_string(), settings.MAX_TOKENS_FOR_HINT))
            # The final output from the LLM is cleaned up into a simple string.
            | StrOutputParser()
        )

        # We invoke the chain by passing the user's input. LangChain automatically
        # uses this input for any part of the chain that needs it (like the retriever).
        # We also pass the user and puzzle info which the prompt template will use.
        response = rag_chain.invoke(
            user_input,
            config={
                "configurable": {
                    "user_name": user_profile.get('name', 'User'),
                    "user_age": user_profile.get('age', 'N/A'),
                    "user_persona": user_profile.get('persona', 'a helpful robot'),
                    "puzzle_question": puzzle.get('question', 'the puzzle')
                }
            }
        )

        return response
