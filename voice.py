from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, VOICE_TYPE

import os

if VOICE_TYPE == "GOOGLE":
    # Fast low quality voice for testing
    import gtts
    import playsound

    def say(string):
        tts = gtts.gTTS(string)
        tts.save("temp.mp3")
        playsound.playsound("temp.mp3")
        return
elif VOICE_TYPE == "ELEVENLABS":
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
        playsound.playsound(new_file_path)
        talking = False
        return
elif VOICE_TYPE == "TEXT":
    def say(string):
        print(string)
        return