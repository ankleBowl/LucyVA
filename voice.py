from config import ELEVENLABS_API_KEY, USE_HIGH_QUALITY_VOICE 

import os

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

        new_file_path = os.path.join("cache", file_name + ".mp3")
        new_file_path = os.path.abspath(new_file_path)

        if not os.path.exists(new_file_path):
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
            with open(new_file_path, "wb") as f:
                f.write(response.content)
        playsound.playsound(new_file_path)
        talking = False
        return

if __name__ == "__main__":
    say("Hello world")