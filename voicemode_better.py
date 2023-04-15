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
    options = whisper.DecodingOptions(fp16=True, language="en")
else:
    options = whisper.DecodingOptions(fp16=False, language="en")

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
        
previous_lucy_commands = []

time_since_command = 10

lucy_in_progress = False

def check_for_wake_word():
    while True:
        global model
        global recording_data
        global user_text
        global previous_lucy_commands
        global time_since_command
        global lucy_in_progress

        if len(recording_data) == 0:
            continue

        audio = np.concatenate(recording_data)
        audio = audio.flatten().astype(np.float32) / 32768.0

        audio = audio[::3]

        for _ in range(len(recording_data) - TARGET_AUDIO_HISTORY):
            recording_data.pop(0)

        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        result = whisper.decode(model, mel, options)

        result = result.text
        result = ''.join([i for i in result if i.isalpha() or i == ' ' or i == '.' or i == '%'])
        result = result.lower()
        
        if WAKE_WORD in result:
            result = result[result.index(WAKE_WORD) + len(WAKE_WORD):].split(".")[0].strip()
            previous_lucy_commands.append(result)
            if not len(previous_lucy_commands) > 3:
                continue
            if get_similarity_score(previous_lucy_commands[-1], previous_lucy_commands[-2]) and get_similarity_score(previous_lucy_commands[-2], previous_lucy_commands[-3]):
                previous_lucy_commands = []
                recording_data = []
                brain.process_request(result)
        else:
            previous_lucy_commands = []

def get_similarity_score(text1, text2):
    text1 = text1.split(" ")
    text2 = text2.split(" ")

    if (len(text1) != len(text2)):
        shorter = text1 if len(text1) < len(text2) else text2
        longer = text2 if len(text1) < len(text2) else text1

        new_longer = []
        skip = False
        for x in range(len(longer)):
            if skip:
                skip = False
                continue
            if x == len(longer) - 1:
                new_longer.append(longer[x])
                break
            combined = longer[x] + longer[x + 1]
            if combined in shorter:
                new_longer.append(combined)
                skip = True
            else:
                new_longer.append(longer[x])
        text1 = shorter
        text2 = new_longer
    
    if len(text1) != len(text2):
        return False

    word_diffs = 0
    for x in range(len(text1)):
        if text1[x] != text2[x]:
            word_diffs += 1

    return not word_diffs > 1

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