from skills.skill import Skill
from config import OPENAI_API_KEY
from voice import say_in_queue

# from skill import Skill

from googlesearch import search as google_search

import openai

import requests
import bs4
import time

openai.api_key = OPENAI_API_KEY

# chrome driver auto installer
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

class Search(Skill):
    def __init__(self):
        super().__init__("Search")
        self.prev_inputs = []

    def load(self):
        return None

    def run(self, input):
        self.log("Received input: " + input)

        for i in range(len(self.prev_inputs)-1, -1, -1):
            if time.time() - self.prev_inputs[i][1] > 120:
                self.prev_inputs = self.prev_inputs[i+1:]
                break

        prompt = "You are rephrasing questions into search queries with keywords. Take context into account.\n\n"
        for i in range(len(self.prev_inputs)):
            prompt += f"{i+1}. {self.prev_inputs[i][0]} - {int(time.time() - self.prev_inputs[i][1])} seconds ago - \"{self.prev_inputs[i][2]}\"\n"
            prompt += f"{self.prev_inputs[i][3]}\n\n"
        prompt += f"{len(self.prev_inputs)+1}. {input} - 0 seconds ago\n\n"
        prompt += "Write a google search query to answer the latest question. Use previous questions for context.\n\n"

        print(prompt)

        keywords = self.query_openai(prompt)

        if keywords[0] == "\"":
            keywords = keywords[1:-1]

        self.log("Searching for: " + keywords)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15"
        }
        response = requests.get("https://html.duckduckgo.com/html?q=" + keywords.replace(" ", "%20"), headers=headers)
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        links = soup.find(id="links")
        results = []
        for i in range(4):
            title = links.find_all(class_="result__title")[i].text.strip()
            description = links.find_all(class_="result__snippet")[i].text.strip()
            results.append((title, description))
        prompt = "You are GoogleGPT. You are trying to answer this question:\n\n"
        prompt += "\"" + input + "\"\n\n"
        prompt += "Here are the top 4 results:\n\n"
        for i in range(4):
            prompt += f"{i+1}. {results[i][0]}\n"
            prompt += f"{results[i][1]}\n\n"
        prompt += "Answer the question using the results. Keep your response very brief and concise.\n\n"

        text = self.query_openai(prompt)

        self.prev_inputs.append((input, time.time(), keywords, text))
        
        say_in_queue(text)

    def query_openai(self, prompt):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        text = completion.choices[0].message["content"]
        return text

if __name__ == "__main__":
    search = Search()
    search.load()
    search.run("What is the meaning of life?")