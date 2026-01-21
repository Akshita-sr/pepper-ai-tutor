#
# pepper_ai_tutor/main_brain_py3/main_controller.py (UPDATED)
#
# ==============================================================================
#  Purpose:
#  This is the master orchestrator for the entire application. It controls the
#  flow of the user interaction from login to logout. This updated version
#  incorporates all the recommended improvements for robustness and design.
# ==============================================================================

import logging
import time
import sys

# --- Import Project-Specific Modules ---
# Import the new utility for standardized logging
from services.utils import setup_logging

# Import the new settings file for global configuration
import settings

# Import all the necessary service classes
from services.database_manager import DatabaseManager
from services.robot_proxy import RobotProxy
from services.llm_gateway import LLMGateway
from services.langchain_orchestrator import LangChainOrchestrator
from services.analytics_manager import AnalyticsManager

# --- Initial Setup ---
# Set up the logger for the entire application. This should be the first thing we do.
setup_logging()
logger = logging.getLogger(__name__)


class PuzzleTutorApp:
    """
    The main application class that encapsulates all logic for the AI Tutor session.
    """

    def __init__(self):
        """
        Initializes all core components of the application.
        """
        logger.info("Initializing PuzzleTutorApp...")

        self.db = DatabaseManager()
        self.robot = RobotProxy(settings.ROBOT_LISTENER_IP)

        # --- NEW: Robustness Check ---
        # Ping the robot listener to make sure it's alive before continuing.
        if not self.robot.ping():
            logger.critical(
                "Could not establish a connection with the robot listener. Please ensure it's running. Exiting.")
            # Exit the application immediately if the robot isn't ready.
            sys.exit(1)

        # These services are initialized after a successful login because they
        # may depend on the specific user who is logged in.
        self.current_user = None
        self.analytics = None
        self.llm_gateway = None
        self.orchestrator = None

        logger.info("PuzzleTutorApp initialized. Waiting for user login.")

    def login(self) -> bool:
        """
        Handles the user login and authentication flow.
        """
        self.robot.say("Hello, please say your username to begin.")

        # The vocabulary should be dynamically created from the users in the database
        # For simplicity, we'll hardcode it based on our users.json file.
        username = self.robot.listen(["Alex", "DrEvans"], timeout=10)

        if not username:
            self.robot.say(
                "I didn't hear a valid name. Please try again later.")
            return False

        # In a real app with more security, you'd listen for digits.
        # For this project, we'll simulate the correct PIN entry.
        self.robot.say(f"Welcome, {username}. Verifying your identity.")
        pin_to_try = "1234" if username == "Alex" else "5678"

        self.current_user = self.db.authenticate_user(username, pin_to_try)

        if self.current_user:
            self.robot.say("Login successful. Let's begin the session.")

            # --- Initialize user-specific services ---
            # Now that we have a user, we can create the services that need a user_id.
            self.analytics = AnalyticsManager(self.db)
            self.llm_gateway = LLMGateway()
            self.orchestrator = LangChainOrchestrator(self.llm_gateway)

            return True
        else:
            self.robot.say(
                "I'm sorry, I could not verify your identity. Goodbye.")
            return False

    def run_puzzle_session(self):
        """
        The main method that controls the puzzle flow after a user has logged in.
        """
        # A list of puzzle IDs to run in this session.
        puzzles_to_play = ["puzzle_01", "puzzle_02", "puzzle_03"]

        for puzzle_id in puzzles_to_play:
            self.run_puzzle(puzzle_id)
            time.sleep(2)  # A brief pause between puzzles
            # Don't say this after the last puzzle
            if puzzle_id != puzzles_to_play[-1]:
                self.robot.say("Great! Let's try the next one.")
                time.sleep(1)

        # --- End of Session ---
        self.robot.say(
            "You've completed all the puzzles for today! You did a fantastic job. Goodbye!")
        self.robot.rest()
        logger.info("Puzzle session finished successfully.")

    def run_puzzle(self, puzzle_id: str):
        """
        Manages the logic for a single puzzle interaction.
        """
        logger.info(
            f"--- Starting puzzle: {puzzle_id} for user: {self.current_user['username']} ---")
        puzzle = self.db.get_puzzle(puzzle_id)
        if not puzzle:
            logger.error(f"Could not find puzzle with ID: {puzzle_id}")
            return

        self.robot.show_image(puzzle['image_url'])
        self.robot.say(puzzle['question'])

        while True:
            vocabulary = ["hint", "help", "quit", "skip"] + \
                puzzle['solution_keywords']
            user_input = self.robot.listen(vocabulary, timeout=15)

            if not user_input:
                self.robot.say(
                    "I'm listening. Say the answer, or ask for a hint.")
                continue

            if user_input.lower() in puzzle['solution_keywords']:
                self.robot.play_animation("celebrate")
                self.robot.say(
                    f"That's it! The answer is {user_input}. Excellent work!")
                break

            elif user_input in ["quit", "skip"]:
                self.robot.say("Okay, skipping this one.")
                break

            else:  # Assumes it's a request for a hint
                self.robot.play_animation("thinking")
                self.robot.say(
                    "That's a good thought. Let me check for a hint.")

                # --- NEW: Controller-managed analytics logging ---
                start_time = time.time()

                # Call the orchestrator to get the hint. Note how we pass the user's profile.
                hint = self.orchestrator.generate_hint(
                    puzzle=puzzle,
                    user_input=user_input,
                    user_profile=self.current_user['profile']
                )

                response_time = time.time() - start_time

                # The controller is now responsible for logging the call.
                self.analytics.log_llm_call(
                    user_id=self.current_user['id'],
                    model_name=settings.LLM_FOR_HINTS,
                    response_time=response_time
                )

                self.robot.say(hint)


def main():
    """
    The main entry point for the AI Brain application.
    """
    logger.info("AI Brain application starting up...")
    try:
        app = PuzzleTutorApp()
        # The session will only run if the login is successful.
        if app.login():
            app.run_puzzle_session()
    except Exception as e:
        logger.critical(
            f"A critical error occurred in the main application loop: {e}", exc_info=True)
        sys.exit(1)

    logger.info("AI Brain shutting down.")


if __name__ == "__main__":
    main()
