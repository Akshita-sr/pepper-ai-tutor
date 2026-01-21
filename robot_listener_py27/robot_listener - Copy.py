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
# It translates these commands (e.g., a JSON message like `{"action": "say", "data": {"text": "Hello!"}}`)
# into actual NAOqi API calls that make the robot perform an action.
#
# This architecture cleanly separates the modern AI logic from the legacy
# robot control system.
#

import qi
import sys
import time
import json
import zmq  # ZeroMQ is used for fast, reliable network communication,  It listens on a specific "address" (TCP port 5555).

# --- !! CRITICAL CONFIGURATION !! ---
# Before running, you MUST change this IP address to match the one for your Pepper robot.
# You can find the robot's IP by pressing the button on its chest once.
ROBOT_IP = "10.186.13.39"  # <<< CHANGE THIS
ROBOT_PORT = 9559


class RobotController:
    """
    A wrapper class that holds all the necessary NAOqi service proxies.
    This keeps the main part of the script clean.
    """

    def __init__(self, session):
        """
        Initializes the controller by getting proxies to all required NAOqi services.
        A "proxy" is a local object that represents a service running on the robot.
        """
        self.session = session
        # Service for basic text-to-speech
        self.tts = session.service("ALTextToSpeech")
        # Service for text-to-speech combined with autonomous animation
        self.animated_speech = session.service("ALAnimatedSpeech")
        # Service for controlling the robot's motion
        self.motion = session.service("ALMotion")
        # Service for displaying content on the robot's tablet
        self.tablet = session.service("ALTabletService")
        # Service for playing pre-made Choregraphe animations
        self.animation_player = session.service("ALAnimationPlayer")
        # Service for recognizing spoken words
        self.speech_recognition = session.service("ALSpeechRecognition")
        # Service for accessing the robot's internal memory (like where recognized words are stored)
        self.memory = session.service("ALMemory")
        

        # Set the language for speech recognition
        self.speech_recognition.setLanguage("English")
        print("[Robot Listener] NAOqi service proxies are ready.")

    def execute_command(self, command):
        """
        Parses a JSON command received over the network and executes the
        corresponding robot action. Returns a JSON response indicating success or failure.
        """
        action = command.get("action")
        data = command.get("data", {})
        print("[Robot Listener] Received command: '{}' with data: {}".format(
            action, data))

        try:
            if action == "say":
                # Use animated speech for more natural-looking interaction
                self.animated_speech.say(str(data.get("text")))
                return {"status": "ok", "action": "say"}

            elif action == "play_animation":
                # IMPORTANT: Assumes you have created animations in Choregraphe and
                # uploaded them to a folder named 'interactive_puzzles' on the robot.
                # Example path on robot: /home/nao/animations/interactive_puzzles/celebrate.anim
                animation_path = "interactive_puzzles/" + data.get("name")
                self.animation_player.run(animation_path)
                return {"status": "ok", "action": "play_animation"}

            elif action == "show_image":
                self.tablet.showImage(str(data.get("url")))
                return {"status": "ok", "action": "show_image"}

            elif action == "rest":
                self.motion.rest()
                return {"status": "ok", "action": "rest"}

            elif action == "listen":
                vocabulary = data.get("vocabulary", [])
                timeout = data.get("timeout", 10)

                # It's good practice to pause the recognizer before changing its settings
                self.speech_recognition.pause(True)
                self.speech_recognition.setVocabulary(vocabulary, False)
                # Unpause to start listening
                self.speech_recognition.pause(False)

                # Subscribe to the event that fires when a word is recognized
                self.speech_recognition.subscribe("WordRecognized")

                recognized_word = ""
                start_time = time.time()

                # Loop for the duration of the timeout, checking for a result
                while time.time() - start_time < timeout:
                    word_data = self.memory.getData("WordRecognized")
                    # Check if a word was heard and if the confidence level is reasonable (e.g., > 40%)
                    if word_data and word_data[0] and word_data[1] > 0.4:
                        recognized_word = word_data[0]
                        # It's crucial to clear the memory event, otherwise you'll hear the same word again
                        self.memory.removeData("WordRecognized")
                        break  # Exit the loop once a word is found
                    time.sleep(0.1)  # Small delay to prevent high CPU usage

                # Unsubscribe from the event to stop listening for it
                self.speech_recognition.unsubscribe("WordRecognized")

                return {"status": "ok", "action": "listen", "result": recognized_word}

            else:
                # If the action name is not recognized
                return {"status": "error", "message": "Unknown action"}

        except Exception as e:
            # Catch any error during NAOqi execution and report it back
            error_message = "Error executing action '{}': {}".format(action, e)
            print("[Robot Listener] " + error_message)
            return {"status": "error", "message": error_message}


def main():
    """
    The main function that sets up the connection to the robot and starts the
    network server.
    """
    # --- Step 1: Connect to the Pepper Robot ---
    try:
        connection_url = "tcp://{}:{}".format(ROBOT_IP, ROBOT_PORT)
        # The qi.Application is the entry point to the NAOqi framework
        app = qi.Application(["RobotListener", "--qi-url=" + connection_url])
        app.start()
    except Exception as e:
        print("[Robot Listener] FATAL: Could not connect to NAOqi at {}:{}. Error: {}. Exiting.".format(
            ROBOT_IP, ROBOT_PORT, e))
        sys.exit(1)

    # Instantiate our controller class
    robot_controller = RobotController(app.session)
    robot_controller.tts.say("Listener activated.")  # Let us know it's running

    # --- Step 2: Setup the ZeroMQ Server ---
    context = zmq.Context()
    # We use a REP (Reply) socket, which waits for a request and then sends a reply
    socket = context.socket(zmq.REP)
    # Bind to port 5555 on all available network interfaces
    socket.bind("tcp://*:5555")
    print("[Robot Listener] ZeroMQ server started on port 5555. Waiting for commands from the AI Brain...")

    # --- Step 3: The Main Server Loop ---
    # This loop runs forever, waiting for and processing commands.
    while True:
        # socket.recv() will block and wait here until a message arrives
        message_str = socket.recv()
        command = json.loads(message_str)

        # Process the command using our controller
        response = robot_controller.execute_command(command)

        # Send the result back to the AI Brain. The brain is waiting for this reply.
        socket.send_json(response)


if __name__ == "__main__":
    main()


"""Of course. Let's break down the theoretical role and function of the robot_listener.py script in a clear, conceptual way.

The Core Concept: A "Puppet Master's Assistant"

Imagine you are a brilliant puppet master (the "AI Brain"). You can think, create stories, and decide what the puppet should do next. However, you are in a separate room and cannot physically touch the puppet's strings.

The robot_listener.py script is your loyal "Assistant" who stands right next to the puppet (the Pepper Robot). The Assistant doesn't know the story or why the puppet needs to move, but they are an expert at pulling the strings.

Your communication works like this:

You (AI Brain): "Hey Assistant, make the puppet wave its hand!"

Assistant (Robot Listener): "Understood." The Assistant pulls the specific strings connected to the puppet's arm to make it wave. Then they reply, "Okay, done."

You (AI Brain): "Now, I need to know if the audience is clapping. Can you listen for me?"

Assistant (Robot Listener): "Sure." The Assistant uses their ears to listen for clapping. If they hear it, they report back, "Yes, I heard clapping." If not, they report, "No, I didn't hear anything."

The robot_listener.py script is this Assistant. It's a specialized, low-level controller whose only job is to translate simple commands from a "smart" remote source into complex physical actions on the robot.

Theoretical Breakdown of the Script's Function
1. The Role: A Command-Execution Server

At its heart, this script is a server. A server is a program that starts, listens for incoming requests on a network, performs a task based on that request, and sends a response back.

The Network: It uses a technology called ZeroMQ (ZMQ) to create a communication channel. Think of ZMQ as a very reliable and fast postal service between the AI Brain and the Robot Listener. It listens on a specific "address" (TCP port 5555).

The Requests: The requests it expects are simple, structured messages in JSON format. JSON is a universal language for data, like {"action": "say", "data": {"text": "Hello!"}}. This is a clean, unambiguous way to give instructions.

The Task: Its task is to execute a command on the robot.

The Response: It always sends a reply back, also in JSON, confirming what it did (e.g., {"status": "ok", "action": "say"}). This is crucial so the AI Brain knows its command was received and completed before it sends the next one.

2. The Primary Responsibility: Interfacing with the NAOqi OS

This is the script's most critical function. It is the only part of the entire project that is allowed to import qi. The qi library is the gateway to NAOqi, the robot's operating system.

Abstraction: It "abstracts away" the complexity of the NAOqi API. The AI Brain doesn't need to know that making the robot speak requires getting a proxy to the ALAnimatedSpeech service and calling the .say() method. The Brain just sends a simple say command. The Listener handles all the low-level details.

Service Proxies: When it starts, it creates "proxies" to all the robot services it might need (ALTextToSpeech, ALMotion, etc.). A proxy is a local Python object that acts as a remote control for the actual service running on the robot. Calling a method on the proxy sends a command to the robot to execute the real method.

3. The Main Workflow (The while True loop)

The theoretical flow of the script's main loop is a classic server pattern:

Block and Wait: The line socket.recv() causes the program to pause indefinitely. It sits there, consuming almost no CPU, simply waiting for a network message to arrive on port 5555.

Receive and Decode: When a message arrives from the AI Brain, socket.recv() "wakes up" and receives the message. It then uses json.loads() to convert the raw text message into a structured Python dictionary.

Dispatch and Execute: The script looks at the action key in the dictionary (e.g., "say", "listen"). It uses an if/elif/else structure to "dispatch" the command to the correct function within the RobotController class. This function then makes the actual qi API call.

Formulate and Reply: After the robot action is complete, the execute_command method creates a response dictionary (e.g., {"status": "ok", ...}). This is converted back into a JSON string and sent back to the AI Brain using socket.send_json().

Loop: The script immediately goes back to Step 1, waiting for the next command.

In Summary: The "Why"

The theoretical reason for this script's existence is to decouple the system.

Decoupling the Python Versions: It allows the modern, powerful AI code (Python 3) to exist separately from the legacy, hardware-specific robot code (Python 2.7).

Decoupling the Logic: It separates the "what to do" (the AI Brain's decision) from the "how to do it" (the Robot Listener's execution). This makes the entire system easier to manage, debug, and upgrade. For example, if you wanted to add a new LLM, you would only have to change the AI Brain; the Robot Listener wouldn't need to be touched at all."""