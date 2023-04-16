from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, VOICE_TYPE

import os
import time
from pydub import AudioSegment
from pydub.playback import play
import threading

if VOICE_TYPE == "GOOGLE":
    # Fast low quality voice for testing
    import gtts

    def say(string):
        tts = gtts.gTTS(string)
        tts.save("temp.mp3")
        sound = AudioSegment.from_mp3("temp.mp3")
        play(sound)
        return
elif VOICE_TYPE == "ELEVENLABS":
    # High quality voice for production
    import requests
    import os

    talking = False

    def say(string):
        global talking
        if talking:
            return
        talking = True

        string = string.strip()
        file_name = string.replace("?", "")

        if len(file_name) > 100:
            file_name = file_name[:100]

        new_file_path = os.path.join("cache", file_name + ".mp3")
        # new_file_path = os.path.abspath(new_file_path)
        if not os.path.exists(new_file_path):
            xi_api_key = ELEVENLABS_API_KEY
            voice_id = ELEVENLABS_VOICE_ID

            headers = {
                "xi-api-key": xi_api_key,
                "Content-Type": "application/json"
            }

            body = {
                "text": string
            }

            response = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", headers=headers, json=body)
            with open(new_file_path, "wb") as f:
                f.write(response.content)
        
        sound = AudioSegment.from_mp3(new_file_path)
        play(sound)
        talking = False
        return
elif VOICE_TYPE == "TEXT":
    def say(string):
        print(string)
        return
    
message_queue = []

def say_in_queue(string):
    global message_queue
    assert type(string) == str
    message_queue.append(string)

def run_queue():
    global message_queue
    while True:
        if len(message_queue) > 0:
            say(message_queue[0])
            message_queue = message_queue[1:]
        time.sleep(0.1)

def play_listening_sfx():
    sound = AudioSegment.from_mp3("sfx/listening.mp3")
    thread = threading.Thread(target=play, args=(sound,))
    thread.start()

def play_loading_sfx():
    sound = AudioSegment.from_mp3("sfx/searching.mp3")
    thread = threading.Thread(target=play, args=(sound,))
    thread.start()


import threading
thread = threading.Thread(target=run_queue)
thread.start()