import pyaudio
import numpy as np
import threading
import whisper
import brain
import torch


CHUNKSIZE = 8192 # fixed chunk size

# MUST BE ALL LOWERCASE AND ONE WORD
WAKE_WORD = "lucy"

model = whisper.load_model("base.en")

TARGET_AUDIO_HISTORY = 20

if torch.cuda.is_available():
    options = whisper.DecodingOptions(fp16=True)
else:
    options = whisper.DecodingOptions()

# initialize portaudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=CHUNKSIZE)

# do this as long as you want fresh samples
recording_data = []
should_be_recording = True

def record_audio_chunk():
    global recording_data

    while True:
        data = stream.read(CHUNKSIZE, exception_on_overflow=False)
        numpydata = np.frombuffer(data, dtype=np.int16).flatten()
        recording_data.append(numpydata)
        
user_text = ""
# last_lucy_command = ""
previous_lucy_commands = []

time_since_command = 10

def check_for_wake_word():
    while True:
        global model
        global recording_data
        global user_text
        global previous_lucy_commands
        global time_since_command

        # if (len(recording_data) < MAX_AUDIO_HISTORY):
        #     analyze = threading.Timer(0.25, check_for_wake_word)
        #     analyze.start();
        #     return

        audio = np.concatenate(recording_data)
        audio = audio.flatten().astype(np.float32) / 32768.0

        audio = audio[::3]

        for _ in range(len(recording_data) - TARGET_AUDIO_HISTORY):
            recording_data.pop(0)

        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        result = whisper.decode(model, mel, options)

        clean_words = [word for word in result.text.split(" ") if word != ""]
        already_spoken_words = user_text.split(" ")

        if len(clean_words) < 3:
            user_text = ""
        elif user_text == "":
            clean_text = ""
            for word in clean_words:
                clean_text += word + " "
            user_text = clean_text
        else:
            word_to_insert_on = 0
            max_score = -1;

            for x in range(len(already_spoken_words)):
                score = 0;
                for y in range(len(clean_words)):
                    if x + y > len(already_spoken_words) - 1:
                        break
                    if already_spoken_words[x + y] == clean_words[y]:
                        score += 1
                if score > max_score:
                    max_score = score
                    word_to_insert_on = x
            
            already_spoken_words = already_spoken_words[:word_to_insert_on]
            for word in clean_words:
                already_spoken_words.append(word)
            user_text = ""
            for word in already_spoken_words:
                user_text += word + " "

        print(user_text)

        time_since_command += 1

        lucy_command = ""
        
        words_bad = user_text.split(" ")
        words = []
        for word in words_bad:
            word = ''.join(e for e in word if e.isalnum() or e == ' ' or e == '%')
            if word != "":
                words.append(word.lower())

        in_command = False
        for x in range(len(words)):
            if WAKE_WORD in words[x]:
                lucy_command = ""
                in_command = True
            elif in_command:
                lucy_command += words[x] + " "
                if '.' in words[x]:
                    in_command = False
                    break

        lucy_command = lucy_command.strip().lower()

        if lucy_command == "":
            previous_lucy_commands = []

        if len(previous_lucy_commands) > 0 and lucy_command != "" and len(lucy_command.split(" ")) == len(previous_lucy_commands[-1].split(" ")):
            time_since_command = 0
            user_text = ""
            recording_data = []
            print("Running command: " + lucy_command)
            brain.process_request(lucy_command)


        previous_lucy_commands.append(lucy_command)
        
        # analyze = threading.Timer(0.01, check_for_wake_word)
        # analyze.start();


thread = threading.Thread(target=record_audio_chunk)
thread.start();

analyze = threading.Timer(2, check_for_wake_word)
analyze.start();

print("Started recording thread")


# # plot data
# plt.plot(numpydata)
# plt.show()

# # close stream
# stream.stop_stream()
# stream.close()
# p.terminate()