import pyttsx3

# Initialize the engine
engine = pyttsx3.init()

# 1. Set properties (Optional but good for testing)
engine.setProperty('rate', 150)    # Speed of speech
engine.setProperty('volume', 1.0)  # Volume level (0.0 to 1.0)

print("SignBridge Voice Test: Initializing...")

# 2. Test a simple sentence
test_message = "Hello Rishi, the Sign Bridge text to speech system is working perfectly."

print(f"Attempting to say: {test_message}")

engine.say(test_message)

# 3. This command is CRITICAL - it tells Python to wait until the speaking is finished
engine.runAndWait()

print("Test Complete. Did you hear the audio?")