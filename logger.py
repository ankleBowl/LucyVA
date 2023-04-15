import time

events = {}

def start_logging(name):
    events[name] = time.time()

def end_logging(name):
    print(name + ": " + str(time.time() - events[name]))