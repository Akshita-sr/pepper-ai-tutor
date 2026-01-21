#
# main_brain_py3/services/robot_proxy.py (UPDATED)
#
import zmq
import json
import logging

logger = logging.getLogger(__name__)

class RobotProxy:
    def __init__(self, zmq_host="localhost", zmq_port=5555, timeout=10000): # 10-second timeout
        self.context = zmq.Context()
        logger.info(f"Connecting to Robot Listener at tcp://{zmq_host}:{zmq_port}...")
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.RCVTIMEO, timeout)
        self.socket.connect(f"tcp://{zmq_host}:{zmq_port}")
        logger.info("Successfully connected to Robot Listener.")

    def _send_command(self, command: dict) -> dict:
        try:
            self.socket.send_json(command)
            response = self.socket.recv_json()
            if response.get("status") == "error":
                logger.error(f"Robot listener reported an error for action '{command.get('action')}': {response.get('message')}")
            return response
        except zmq.error.Again:
            logger.error(f"ZMQ Error: No response from robot listener for action '{command.get('action')}'. The listener might be down.")
            return {"status": "error", "message": "No response from listener"}
        except Exception as e:
            logger.error(f"An unexpected error occurred during ZMQ communication: {e}")
            return {"status": "error", "message": str(e)}

    # --- NEW METHOD TO ADD ---
    def ping(self) -> bool:
        """
        Sends a simple 'ping' command to check if the listener is alive and responsive.
        
        Returns:
            bool: True if the listener responded correctly, False otherwise.
        """
        logger.info("Pinging robot listener to check connection...")
        command = {"action": "ping", "data": {}}
        response = self._send_command(command)
        is_alive = response.get("status") == "ok"
        if is_alive:
            logger.info("Ping successful. Listener is alive.")
        else:
            logger.error("Ping failed. Listener did not respond correctly.")
        return is_alive

    # --- Public High-Level Methods ---
    def say(self, text: str):
        logger.info(f"Sending SAY command: '{text}'")
        command = {"action": "say", "data": {"text": text}}
        return self._send_command(command)

    def play_animation(self, animation_name: str):
        logger.info(f"Sending ANIMATE command: '{animation_name}'")
        command = {"action": "play_animation", "data": {"name": animation_name}}
        return self._send_command(command)
    
    # ... The rest of the file (show_image, listen, rest) remains the same ...
    def show_image(self, url: str):
        logger.info(f"Sending TABLET command: '{url}'")
        command = {"action": "show_image", "data": {"url": url}}
        return self._send_command(command)

    def listen(self, vocabulary: list, timeout: int = 10) -> str:
        logger.info(f"Sending LISTEN command: Vocab={vocabulary}, Timeout={timeout}s")
        command = {"action": "listen", "data": {"vocabulary": vocabulary, "timeout": timeout}}
        response = self._send_command(command)
        recognized_word = response.get("result", "")
        if recognized_word:
            logger.info(f"Listener heard: '{recognized_word}'")
        else:
            logger.warning("Listener timed out or heard nothing.")
        return recognized_word

    def rest(self):
        logger.info("Sending REST command.")
        command = {"action": "rest", "data": {}}
        return self._send_command(command)