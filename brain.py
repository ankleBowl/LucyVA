from voice import say

say("I'm starting up. Please wait a moment.")

from skills.skill import Skill
from skills.spotify import Spotify
from skills.lights import Lights
from similarity import get_similarity

skills = [
    Spotify(),
    Lights()
]

for skill in skills:
    response = skill.load()
    if response != None:
        say(response)
    print("[BRAIN] Loaded skill: " + skill.name)


def process_request(input):
    print("[BRAIN] Processing request: " + input)

    global skills
    currentSkill = None
    highestSimilarity = 0
    for skill in skills:
        similarity = skill.get_similarity(input)
        if similarity > highestSimilarity:
            highestSimilarity = similarity
            currentSkill = skill
    print("[BRAIN] Decided to use skill: " + currentSkill.name + " | " + str(highestSimilarity))
    response = currentSkill.run(input)
    if response != None:
        say(response)

say("I'm ready. Ask me anything.")