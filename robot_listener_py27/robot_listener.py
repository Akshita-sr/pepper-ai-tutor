#
# pepper_llm_final/robot_listener_py27/robot_listener.py
#
# ==============================================================================
#  IMPORTANT: THIS SCRIPT MUST BE RUN WITH PYTHON 2.7
# ==============================================================================
#
# Purpose:
# This script is the dedicated "Robot Controller." It acts as a server.
#
# CURRENT CONFIGURATION: **CHOREGRAPHE SIMULATION MODE**
# - Uses localhost
# - Uses keyboard typing instead of speech recognition
# - Simulates tablet display in console
#

import qi
import sys
import time
import json
import zmq  # ZeroMQ for network communication

# ==============================================================================
# CONFIGURATION SECTION
# ==============================================================================

# --- [OPTION 1: CHOREGRAPHE SIMULATION] (ACTIVE) ---
# Use localhost. CHECK THE PORT in Choregraphe -> Connection -> Connect to...
ROBOT_IP = "127.0.0.1"
ROBOT_PORT = 9559  # <--- !!! CHANGE THIS TO YOUR CHOREGRAPHE PORT !!!

# --- [OPTION 2: REAL PEPPER ROBOT] (COMMENTED OUT) ---
# Use the real IP of your robot (press chest button to hear it)
# ROBOT_IP = "192.168.1.100" 
# ROBOT_PORT = 9559

# ==============================================================================

class RobotController:
    """
    A wrapper class that holds all the necessary NAOqi service proxies.
    """

    def __init__(self, session):
        self.session = session
        
        # --- Service Proxies ---
        # We attempt to get all proxies. In simulation, some might be simulated.
        try:
            self.tts = session.service("ALTextToSpeech")
            self.animated_speech = session.service("ALAnimatedSpeech")
            self.motion = session.service("ALMotion")
            self.behavior_manager = session.service("ALBehaviorManager")
            self.memory = session.service("ALMemory")
            
            # These services might fail or act differently in Choregraphe
            self.tablet = session.service("ALTabletService")
            self.speech_recognition = session.service("ALSpeechRecognition")
            
            # Set language if speech recognition is available
            try:
                self.speech_recognition.setLanguage("English")
            except Exception:
                print("[Init Warning] Could not set language. Speech Reco might be inactive in Sim.")
                
            print("[Robot Listener] NAOqi service proxies are ready.")
            
        except Exception as e:
            print("[Init Error] Failed to get some services: {}".format(e))

    def execute_command(self, command):
        """
        Parses a JSON command and executes the corresponding robot action.
        """
        action = command.get("action")
        data = command.get("data", {})
        print("[Robot Listener] Received command: '{}'".format(action))

        try:
            # --- 1. SAY (Works in both) ---
            if action == "say":
                text_to_say = str(data.get("text"))
                # In sim, sometimes animated speech doesn't show movement, but TTS works
                self.animated_speech.say(text_to_say)
                return {"status": "ok", "action": "say"}

            # --- 2. PING (Works in both) ---
            elif action == "ping":
                return {"status": "ok", "action": "ping"}

            # --- 3. ANIMATION (Works in both if behavior exists) ---
            elif action == "play_animation":
                behavior_name = data.get("name")
                if self.behavior_manager.isBehaviorInstalled(behavior_name):
                    self.behavior_manager.runBehavior(behavior_name)
                    return {"status": "ok", "action": "play_animation"}
                else:
                    error_msg = "Behavior '{}' not found.".format(behavior_name)
                    print("[Error] " + error_msg)
                    return {"status": "error", "message": error_msg}

            # --- 4. SHOW IMAGE (SWITCHED FOR SIMULATION) ---
            elif action == "show_image":
                url = str(data.get("url"))
                
                # --- [SIMULATION MODE] ---
                try:
                    # Try to use the service, but print to console regardless
                    self.tablet.showImage(url)
                    print("\n[SIMULATION TABLET] Displaying Image: {}\n".format(url))
                except Exception:
                    print("\n[SIMULATION TABLET] (Service Unavailable) Imagine showing: {}\n".format(url))
                return {"status": "ok", "action": "show_image"}

                # --- [REAL ROBOT MODE] (COMMENTED OUT) ---
                # self.tablet.showImage(url)
                # return {"status": "ok", "action": "show_image"}

            # --- 5. REST (Works in both) ---
            elif action == "rest":
                self.motion.rest()
                return {"status": "ok", "action": "rest"}

            # --- 6. LISTEN (SWITCHED FOR SIMULATION) ---
            elif action == "listen":
                vocabulary = data.get("vocabulary", [])
                timeout = data.get("timeout", 10)

                # --- [SIMULATION MODE] (KEYBOARD INPUT) ---
                print("\n" + "="*40)
                print("[SIMULATION INPUT REQUIRED]")
                print("The Robot is listening for: {}".format(vocabulary))
                print("Please TYPE your answer below:")
                print("="*40 + "\n")

                # Python 2 'raw_input' reads text from the terminal
                user_typed = raw_input("YOU SAY: ")
                return {"status": "ok", "action": "listen", "result": user_typed}

                # --- [REAL ROBOT MODE] (SPEECH RECOGNITION) (COMMENTED OUT) ---
                # self.speech_recognition.pause(True)
                # self.speech_recognition.setVocabulary(vocabulary, False)
                # self.speech_recognition.pause(False)
                # self.speech_recognition.subscribe("WordRecognized")
                # recognized_word = ""
                # start_time = time.time()
                # while time.time() - start_time < timeout:
                #     word_data = self.memory.getData("WordRecognized")
                #     if word_data and word_data[0] and word_data[1] > 0.4:
                #         recognized_word = word_data[0]
                #         self.memory.removeData("WordRecognized")
                #         break
                #     time.sleep(0.1)
                # self.speech_recognition.unsubscribe("WordRecognized")
                # return {"status": "ok", "action": "listen", "result": recognized_word}

            else:
                return {"status": "error", "message": "Unknown action"}

        except Exception as e:
            error_message = "Error executing action '{}': {}".format(action, e)
            print("[Robot Listener Error] " + error_message)
            return {"status": "error", "message": error_message}


def main():
    print("--------------------------------------------------")
    print("   ROBOT LISTENER (PYTHON 2.7) - SIMULATION MODE  ")
    print("--------------------------------------------------")
    print("Connecting to Choregraphe at {}:{}...".format(ROBOT_IP, ROBOT_PORT))
    
    try:
        connection_url = "tcp://{}:{}".format(ROBOT_IP, ROBOT_PORT)
        app = qi.Application(["RobotListener", "--qi-url=" + connection_url])
        app.start()
    except Exception as e:
        print("\n[FATAL ERROR] Could not connect to Choregraphe!")
        print("Details: {}".format(e))
        print("1. Is Choregraphe open?")
        print("2. Is the Virtual Robot active?")
        print("3. DID YOU UPDATE 'ROBOT_PORT' IN THIS SCRIPT TO MATCH CHOREGRAPHE?")
        sys.exit(1)

    robot_controller = RobotController(app.session)
    robot_controller.tts.say("Connected to brain.")

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    print("\n[ZeroMQ] Server started on port 5555.")
    print("[ZeroMQ] Waiting for commands from Python 3 Brain...\n")

    while True:
        # Wait for next request from client
        message_str = socket.recv()
        command = json.loads(message_str)
        
        # Process request
        response = robot_controller.execute_command(command)
        
        # Send reply back to client
        socket.send_json(response)


if __name__ == "__main__":
    main()