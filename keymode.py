import pynput
import whisper
import brain
import sounddevice as sd
from scipy.io.wavfile import write

# when right shift key is pressed, call a function that records 7 seconds of audio and then processes it with whisper and brain

model = whisper.load_model("base.en")

def on_press(key):
    if key == pynput.keyboard.Key.shift_r:
        print("Shift pressed")
        myrecording = sd.rec(int(4 * 44100), samplerate=44100, channels=1)
        sd.wait()
        write('output.wav', 44100, myrecording)

        audio = whisper.load_audio("output.wav")
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        options = whisper.DecodingOptions()
        result = whisper.decode(model, mel, options)
        print(result.text)
        # remove non alphanumeric characters
        text = ''.join(e for e in result.text if e.isalnum() or e == ' ')
        brain.process_request(text)

# add the listener
with pynput.keyboard.Listener(on_press=on_press) as listener:
    listener.join()