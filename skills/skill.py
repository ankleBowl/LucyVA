class Skill:
    def __init__(self, name):
        self.name = name

    def get_similarity(self):
        pass

    def run(self, input):
        pass

    def voice_activity_detected(self):
        pass

    def voice_activity_ended(self):
        pass

    def log(self, message):
        print("[" + self.name + "] " + message)
    
    def load(self):
        pass