import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    print(f"ID: {voice.id}")
engine.say("Checking voice connection")
engine.runAndWait()