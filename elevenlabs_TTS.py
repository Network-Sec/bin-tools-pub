# Text To Speech
# Example, use "s" to say something:
# (tts) s Hello Sir please pay me all the money now
# Documented commands (type help <topic>):
# ========================================
# exit  help  s  voice  voices
# (tts) voices
# Available voice models:
# - Drew
# - Clyde
# - Dave
# - Antoni
# - Thomas
# ...
# (tts) voice Dave

import os
import cmd
from elevenlabs.client import ElevenLabs
from elevenlabs import play

# Initialize ElevenLabs client with your API key
API_KEY = "..." 
client = ElevenLabs(api_key=API_KEY)

class TextToSpeechApp(cmd.Cmd):
    intro = "Welcome to the ElevenLabs Text-to-Speech CLI App. Type help or ? to list commands.\n"
    prompt = "(tts) "
    current_voice = "Daniel"

    def do_s(self, arg):
        "Generate and play speech from text: [text]"
        if not arg:
            print("Please provide text to generate speech.")
            return
        self.generate_and_play(arg)

    def do_exit(self, arg):
        "Exit the application."
        print("Exiting...")
        return True

    def generate_and_play(self, text):
        try:
            # Generate the audio using ElevenLabs API
            audio = client.generate(
                text=text,
                voice=self.current_voice,
                model="eleven_multilingual_v2"
            )

            # Play the generated audio
            play(audio)

            # Save generated text to a file
            self.save_to_file(text, audio)

        except Exception as e:
            print(f"An error occurred: {e}")

    def save_to_file(self, text, audio):
        # Create a directory to store generated text files if it doesn't exist
        if not os.path.exists("generated_text"):
            os.makedirs("generated_text")

        # Prepare filename (replace special chars and spaces with underscore, and lowercase)
        filename = text.lower().replace(" ", "_")
        filename = "".join([c if c.isalnum() or c == "_" else "_" for c in filename])

        # Save the text to a file - doesn't work yet, files are 0 bytes
        # An error occurred: a bytes-like object is required, not 'generator'
        with open(os.path.join("generated_text", f"{filename}.mp3"), "wb") as file:
            file.write(b"".join(audio))

    def do_voices(self, arg):
        "List all available voice models"
        voices = client.voices.get_all()
        if voices:
            print("Available voice models:")
            for voice in voices.voices:
                print(f"- {voice.name}")
        else:
            print("No available voice models found.")

    def do_voice(self, arg):
        "Set the current voice model: voice <Name>"
        if arg:
            self.current_voice = arg
            print(f"Current voice set to: {self.current_voice}")
        else:
            print("Please provide a voice name.")

    def do_EOF(self, line):
        return True

if __name__ == '__main__':
    TextToSpeechApp().cmdloop()
