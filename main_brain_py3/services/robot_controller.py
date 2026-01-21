import qi
import time

class RobotController:
    """A wrapper class to simplify interactions with the Pepper robot's NAOqi API."""
    
    def __init__(self, session):
        self.session = session
        # Get proxies to all necessary services
        self.tts = session.service("ALTextToSpeech")
        self.animated_speech = session.service("ALAnimatedSpeech")
        self.motion = session.service("ALMotion")
        self.tablet = session.service("ALTabletService")
        self.animation_player = session.service("ALAnimationPlayer")
        self.speech_recognition = session.service("ALSpeechRecognition")
        self.memory = session.service("ALMemory")
        self.awareness = session.service("ALBasicAwareness")
        
        # Configure speech recognition
        self.speech_recognition.setLanguage("English")
        self.is_listening = False
        print("Robot Controller: Proxies to NAOqi services are ready.")

    def _get_animation_path(self, animation_name):
        # IMPORTANT: Change this path to where you uploaded your animations on the robot!
        return "interactive_puzzles/" + animation_name

    def say(self, text, animated=True):
        """Makes the robot speak. Uses animated speech by default."""
        print("ROBOT SAYS: {}".format(text))
        if animated:
            self.animated_speech.say(text)
        else:
            self.tts.say(text)

    def play_animation(self, animation_name):
        """Plays a pre-made animation from Choregraphe."""
        full_path = self._get_animation_path(animation_name)
        print("ROBOT ANIMATES: {}".format(full_path))
        try:
            self.animation_player.run(full_path)
        except Exception as e:
            print("Error playing animation {}: {}".format(full_path, e))

    def listen(self, vocabulary, timeout=5):
        """Listens for a word from a specific vocabulary list."""
        self.is_listening = True
        self.speech_recognition.pause(True)
        self.speech_recognition.setVocabulary(vocabulary, False)
        self.speech_recognition.pause(False)
        self.speech_recognition.subscribe("WordRecognized")
        
        print("ROBOT LISTENS: (Vocab: {})".format(vocabulary))
        recognized_word = ""
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            word_data = self.memory.getData("WordRecognized")
            if word_data and word_data[0] and word_data[1] > 0.4: # Word and confidence score
                recognized_word = word_data[0]
                print("ROBOT HEARD: '{}' with confidence {}".format(word_data[0], word_data[1]))
                self.memory.removeData("WordRecognized") # Clear the memory
                break
            time.sleep(0.1)

        self.speech_recognition.unsubscribe("WordRecognized")
        self.is_listening = False
        return recognized_word

    def show_image(self, url):
        """Displays an image on the tablet."""
        print("ROBOT TABLET: Showing image at {}".format(url))
        self.tablet.showImage(url)

    def hide_tablet(self):
        """Hides the tablet content."""
        print("ROBOT TABLET: Hiding content.")
        self.tablet.hide()

    def set_awareness(self, status):
        """Turns basic awareness (autonomous head movements) on or off."""
        print("ROBOT AWARENESS: {}".format("On" if status else "Off"))
        if status:
            self.awareness.setEnabled(True)
        else:
            self.awareness.setEnabled(False)

    def rest(self):
        """Puts the robot in a resting position."""
        self.motion.rest()