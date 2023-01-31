from config import ELEVENLABS_API_KEY, USE_HIGH_QUALITY_VOICE 

import os

path_separator = "/"
if os.name == "nt":
    path_separator = "\\"

if not USE_HIGH_QUALITY_VOICE:
    # Fast low quality voice for testing
    import gtts
    import playsound

    def say(string):
        tts = gtts.gTTS(string)
        tts.save("temp.mp3")
        playsound.playsound("temp.mp3")
        return
else:
    # High quality voice for production
    import requests
    import playsound
    import os

    talking = False

    def say(string):
        global talking
        if talking:
            return
        talking = True

        string = string.strip()
        file_name = string.replace("?", "")
        if not os.path.exists("cache" + path_separator + file_name + ".mp3"):
            xi_api_key = ELEVENLABS_API_KEY
            voice_id = "EXAVITQu4vr4xnSDxMaL"

            headers = {
                "xi-api-key": xi_api_key,
                "Content-Type": "application/json"
            }

            body = {
                "text": string
            }

            response = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", headers=headers, json=body)
            with open("cache" + path_separator + file_name + ".mp3", "wb") as f:
                f.write(response.content)
        playsound.playsound("cache" + path_separator + file_name + ".mp3")
        talking = False
        return