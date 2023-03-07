from transformers import AutoTokenizer, AutoModelForSequenceClassification
tokenizer = AutoTokenizer.from_pretrained("shahrukhx01/question-vs-statement-classifier")
model = AutoModelForSequenceClassification.from_pretrained("shahrukhx01/question-vs-statement-classifier")

from skills.skill import Skill
from config import OPENAI_API_KEY
# from googlesearch import search
# import requests
import bs4 as bs
import openai

openai.api_key = OPENAI_API_KEY

class Search(Skill):
    def __init__(self):
        super().__init__("Search")

        self.conv_history = []
    
    def load(self):
        pass

    def get_similarity(self, userInput):
        inputs = tokenizer(userInput, return_tensors="pt")
        outputs = model(**inputs)
        isQuestion = outputs.logits.argmax().item() == 1
        if not isQuestion:
            return 0;
        return 0.5;

    def run(self, userInput):
        if len(self.conv_history) > 8:
            self.conv_history = self.conv_history[2:]

        self.conv_history.append(userInput)

        prefix = "The following conversation is between a virtual assistant and user\n\n"
        for x in range(len(self.conv_history)):
            if x % 2 == 0:
                prefix += "User: " + self.conv_history[x] + "\n\n"
            else:
                prefix += "Assistant: " + self.conv_history[x] + "\n\n"
        prefix += "Assistant:"

        self.log("Querying GPT-3 with " + userInput)

        openai_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prefix,
            temperature=0,
            max_tokens=150,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0.6,
            stop=["User:", "Assistant:"]
        )
        return_text = openai_response.choices[0].text
        return_text = return_text.strip()

        self.conv_history.append(return_text)
        self.log("Response: " + return_text)
        return return_text


    # def tag_visible(self, element):
    #     if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
    #         return False
    #     if isinstance(element, bs.element.Comment):
    #         return False
    #     return True


    # def text_from_html(self, body):
    #     soup = bs.BeautifulSoup(body, 'html.parser')
    #     texts = soup.findAll(text=True)
    #     visible_texts = filter(self.tag_visible, texts)  
    #     real_visible_texts = []
    #     for text in visible_texts:
    #         if len(text.split(" ")) > 10:
    #             real_visible_texts.append(text)
    #     text = " ".join(t.strip() for t in real_visible_texts)
    #     if len(text) > 500:
    #         text = text[:500] + "..."
    #     return text

if __name__ == "__main__":
    search_skill = Search()
    print(search_skill.run("What is the meaning of life."))