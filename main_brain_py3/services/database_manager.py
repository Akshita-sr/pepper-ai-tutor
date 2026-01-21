#
# main_brain_py3/services/database_manager.py (UPDATED)
#
import sqlite3
import json
import logging
import bcrypt

logger = logging.getLogger(__name__)


def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def check_pin(pin: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pin.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


class DatabaseManager:
    def __init__(self, db_path="tutor.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Database connection established to {db_path}.")

    def execute_query(self, query, params=(), fetch=None):
        try:
            c = self.conn.cursor()
            c.execute(query, params)
            if fetch == 'one':
                result = c.fetchone()
                return dict(result) if result else None
            elif fetch == 'all':
                results = c.fetchall()
                return [dict(row) for row in results]
            else:
                self.conn.commit()
                return c.lastrowid
        except Exception as e:
            logger.error(f"Database query failed: {e}", exc_info=True)
            raise

    def setup_tables(self):
        # User table with profile data
        self.execute_query('''CREATE TABLE IF NOT EXISTS users
                             (id INTEGER PRIMARY KEY,
                              username TEXT UNIQUE NOT NULL,
                              pin_hash TEXT NOT NULL,
                              profile_json TEXT)''')
        # Puzzle metadata table
        self.execute_query('''CREATE TABLE IF NOT EXISTS puzzles
                              (puzzle_id TEXT PRIMARY KEY, 
                               question TEXT, 
                               image_url TEXT, 
                               solution_keywords_json TEXT)''')
        # Analytics table
        self.execute_query('''CREATE TABLE IF NOT EXISTS usage_analytics
                             (id INTEGER PRIMARY KEY, 
                              user_id INTEGER, 
                              model_name TEXT, 
                              response_time REAL, 
                              timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                              FOREIGN KEY(user_id) REFERENCES users(id))''')
        logger.info("Database tables created/verified.")

    def add_user(self, username, pin, profile_dict):
        pin_hash = hash_pin(pin)
        profile_json = json.dumps(profile_dict)
        try:
            self.execute_query(
                "INSERT OR REPLACE INTO users (username, pin_hash, profile_json) VALUES (?, ?, ?)", (username, pin_hash, profile_json))
        except sqlite3.IntegrityError:
            logger.warning(f"User '{username}' already exists.")

    def authenticate_user(self, username, pin):
        user_row = self.execute_query(
            "SELECT * FROM users WHERE username = ?", (username,), fetch='one')
        if user_row and check_pin(pin, user_row['pin_hash']):
            user_row['profile'] = json.loads(user_row['profile_json'])
            return user_row
        return None

    # --- NEW METHODS TO ADD ---

    def add_puzzle(self, puzzle_id: str, question: str, image_url: str, solution_keywords: list):
        """Adds or updates a puzzle's metadata in the database."""
        keywords_json = json.dumps(solution_keywords)
        try:
            self.execute_query(
                "INSERT OR REPLACE INTO puzzles (puzzle_id, question, image_url, solution_keywords_json) VALUES (?, ?, ?, ?)",
                (puzzle_id, question, image_url, keywords_json)
            )
        except Exception as e:
            logger.error(f"Failed to add puzzle {puzzle_id} to database: {e}")

    def get_puzzle(self, puzzle_id: str) -> dict:
        """Retrieves a single puzzle's metadata from the database by its ID."""
        puzzle_row = self.execute_query(
            "SELECT * FROM puzzles WHERE puzzle_id = ?", (puzzle_id,), fetch='one')
        if puzzle_row:
            # Convert the solution keywords from a JSON string back into a Python list
            puzzle_row['solution_keywords'] = json.loads(
                puzzle_row['solution_keywords_json'])
        return puzzle_row
