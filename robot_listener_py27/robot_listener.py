#
# pepper_llm_final/robot_listener_py27/robot_listener.py
#
# ==============================================================================
#  IMPORTANT: THIS SCRIPT MUST BE RUN WITH PYTHON 2.7
# ==============================================================================
#
# Purpose:
# This script is the dedicated "Robot Controller." It acts as a server that runs
# directly on a machine that can communicate with the Pepper robot. Its sole
# responsibility is to listen for simple, high-level commands over the network
# from the main "AI Brain" (the Python 3 application).
#
# This updated version uses ALBehaviorManager for running animations, which is
# the standard and most reliable method.
#

import qi
import sys
import time
import json
import zmq  # ZeroMQ for network communication

# --- !! CRITICAL CONFIGURATION !! ---
# Before running, you MUST change this IP address to match your Pepper robot's.
ROBOT_IP = "10.186.13.39"  # <<< CHANGE THIS
ROBOT_PORT = 9559


class RobotController:
    """
    A wrapper class that holds all the necessary NAOqi service proxies.
    """

    def __init__(self, session):
        """
        Initializes the controller by getting proxies to all required NAOqi services.
        """
        self.session = session
        # --- Service Proxies ---
        self.tts = session.service("ALTextToSpeech")
        self.animated_speech = session.service("ALAnimatedSpeech")
        self.motion = session.service("ALMotion")
        self.tablet = session.service("ALTabletService")
        # OLD: self.animation_player = session.service("ALAnimationPlayer") # We no longer use this.
        self.speech_recognition = session.service("ALSpeechRecognition")
        self.memory = session.service("ALMemory")

        # --- THE KEY CHANGE IS HERE ---
        # ALBehaviorManager is the service that runs behaviors installed on the robot.
        self.behavior_manager = session.service("ALBehaviorManager")

        # Set the language for speech recognition
        self.speech_recognition.setLanguage("English")
        print("[Robot Listener] NAOqi service proxies are ready.")

    def execute_command(self, command):
        """
        Parses a JSON command and executes the corresponding robot action.
        """
        action = command.get("action")
        data = command.get("data", {})
        print("[Robot Listener] Received command: '{}' with data: {}".format(
            action, data))

        try:
            if action == "say":
                self.animated_speech.say(str(data.get("text")))
                return {"status": "ok", "action": "say"}

            elif action == "ping":
                return {"status": "ok", "action": "ping"}
            # --- THE UPDATED ANIMATION BLOCK ---
            elif action == "play_animation":
                # The 'name' sent from the AI Brain should match the name of the
                # Behavior you create in Choregraphe (e.g., "celebrate", "thinking").
                behavior_name = data.get("name")

                # First, check if the behavior is actually installed on the robot.
                if self.behavior_manager.isBehaviorInstalled(behavior_name):
                    # Use runBehavior, which is non-blocking by default.
                    # The listener can immediately go back to waiting for the next command.
                    self.behavior_manager.runBehavior(behavior_name)
                    return {"status": "ok", "action": "play_animation"}
                else:
                    # If the behavior doesn't exist, report a clear error.
                    error_msg = "Behavior '{}' is not installed on the robot. Please check Choregraphe.".format(
                        behavior_name)
                    print("[Robot Listener] " + error_msg)
                    return {"status": "error", "message": error_msg}

            elif action == "show_image":
                self.tablet.showImage(str(data.get("url")))
                return {"status": "ok", "action": "show_image"}

            elif action == "rest":
                self.motion.rest()
                return {"status": "ok", "action": "rest"}

            elif action == "listen":
                vocabulary = data.get("vocabulary", [])
                timeout = data.get("timeout", 10)

                self.speech_recognition.pause(True)
                self.speech_recognition.setVocabulary(vocabulary, False)
                self.speech_recognition.pause(False)

                self.speech_recognition.subscribe("WordRecognized")

                recognized_word = ""
                start_time = time.time()

                while time.time() - start_time < timeout:
                    word_data = self.memory.getData("WordRecognized")
                    if word_data and word_data[0] and word_data[1] > 0.4:
                        recognized_word = word_data[0]
                        self.memory.removeData("WordRecognized")
                        break
                    time.sleep(0.1)

                self.speech_recognition.unsubscribe("WordRecognized")

                return {"status": "ok", "action": "listen", "result": recognized_word}

            else:
                return {"status": "error", "message": "Unknown action"}

        except Exception as e:
            error_message = "Error executing action '{}': {}".format(action, e)
            print("[Robot Listener] " + error_message)
            return {"status": "error", "message": error_message}

# --- The main() function remains the same ---


def main():
    try:
        connection_url = "tcp://{}:{}".format(ROBOT_IP, ROBOT_PORT)
        app = qi.Application(["RobotListener", "--qi-url=" + connection_url])
        app.start()
    except Exception as e:
        print("[Robot Listener] FATAL: Could not connect to NAOqi at {}:{}. Error: {}. Exiting.".format(
            ROBOT_IP, ROBOT_PORT, e))
        sys.exit(1)

    robot_controller = RobotController(app.session)
    robot_controller.tts.say("Listener activated. Behavior manager is ready.")

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    print("[Robot Listener] ZeroMQ server started on port 5555. Waiting for commands...")

    while True:
        message_str = socket.recv()
        command = json.loads(message_str)
        response = robot_controller.execute_command(command)
        socket.send_json(response)


if __name__ == "__main__":
    main()
