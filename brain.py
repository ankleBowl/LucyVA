from voice import say_in_queue, play_loading_sfx
import os

os.environ["TOKENIZERS_PARALLELISM"] = "true"

def log(message):
    print("[BRAIN] " + message)

log("Starting up...") 
say_in_queue("I'm starting up. Please wait a moment.")

from skills.skill import Skill
from skills.spotify import Spotify
from skills.lights import Lights
from skills.search import Search

import threading

import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

from transformers import AutoModelForSequenceClassification, AutoTokenizer
model = AutoModelForSequenceClassification.from_pretrained("ankleBowl/autotrain-conversation-classifier-47670119801")
tokenizer = AutoTokenizer.from_pretrained("ankleBowl/autotrain-conversation-classifier-47670119801")

skills = {
    2: Search(),
    1: Spotify(),
    0: Lights(),
}

def load_skill(skill):
    response = skill.load()
    if response != None:
        say_in_queue(response)
    log("Loaded skill: " + skill.name)

threads = []

for skill in skills:
    skill = skills[skill]
    thread = threading.Thread(target=load_skill, args=(skill,))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

log("All skills loaded")

def voice_activity_detected():
    for skill in skills:
        skill = skills[skill]
        skill.voice_activity_detected()

def voice_activity_ended():
    for skill in skills:
        skill = skills[skill]
        skill.voice_activity_ended()


def process_request(input):
    play_loading_sfx()
    start_logging("brain.process_request.get_similarity")
    inputs = tokenizer(input, return_tensors="pt")
    outputs = model(**inputs)
    outputs = outputs.logits.tolist()[0]
    highest = max(outputs)
    skill_id = outputs.index(highest)
    if highest < 3.75:
        skill_id = 2
    currentSkill = skills[skill_id]
    end_logging("brain.process_request.get_similarity")

    start_logging("brain.process_request.run")
    currentSkill.run(input)
    end_logging("brain.process_request.run")


say_in_queue("I'm ready. Ask me anything.")




import time

events = {}

def start_logging(name):
    events[name] = time.time()

def end_logging(name):
    print(name + ": " + str(time.time() - events[name]))