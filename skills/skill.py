class Skill:
    def __init__(self, name):
        self.name = name

    def get_similarity(self):
        pass

    def run(self, input):
        pass

    def log(self, message):
        print("[" + self.name + "] " + message)
    
    def load(self):
        pass