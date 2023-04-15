from voice import say
import os

import logger

os.environ["TOKENIZERS_PARALLELISM"] = "true"

def log(message):
    print("[BRAIN] " + message)

log("Starting up...") 
say("I'm starting up. Please wait a moment.")

from skills.skill import Skill
from skills.spotify import Spotify
# from skills.lights import Lights
# from skills.search import Search

import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

from transformers import AutoModelForSequenceClassification, AutoTokenizer
model = AutoModelForSequenceClassification.from_pretrained("ankleBowl/autotrain-conversation-classifier-47670119801")
tokenizer = AutoTokenizer.from_pretrained("ankleBowl/autotrain-conversation-classifier-47670119801")

skills = {
    1: Spotify(),
    # "0": Lights(),
}

for skill in skills:
    skill = skills[skill]
    response = skill.load()
    if response != None:
        say(response)
    log("Loaded skill: " + skill.name)

def voice_activity_detected():
    for skill in skills:
        skill = skills[skill]
        skill.voice_activity_detected()

def voice_activity_ended():
    for skill in skills:
        skill = skills[skill]
        skill.voice_activity_ended()

def process_request(input):
    logger.start_logging("brain.process_request.get_similarity")
    inputs = tokenizer(input, return_tensors="pt")
    outputs = model(**inputs)
    skill_id = outputs.logits.argmax().item()
    currentSkill = skills[skill_id]
    logger.end_logging("brain.process_request.get_similarity")

    logger.start_logging("brain.process_request.run")
    currentSkill.run(input)
    logger.end_logging("brain.process_request.run")


# say("I'm ready. Ask me anything.")