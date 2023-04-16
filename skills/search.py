from skills.skill import Skill
from config import OPENAI_API_KEY
from voice import say_in_queue

# from skill import Skill

from googlesearch import search as google_search

import openai

import requests
import bs4

openai.api_key = OPENAI_API_KEY

# chrome driver auto installer
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

class Search(Skill):
    def __init__(self):
        super().__init__("Search")

    def load(self):
        return None

    def run(self, input):
        with open("search.txt", "a") as f:
            f.write(input + "\n")

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15"
        }
        response = requests.get("https://html.duckduckgo.com/html?q=" + input.replace(" ", "%20"), headers=headers)
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
        prompt += "Answer the question using the results. Keep your response as brief and concise as possible.\n\n"

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        text = completion.choices[0].message["content"]
        say_in_queue(text)

if __name__ == "__main__":
    search = Search()
    search.load()
    search.run("What is the meaning of life?")