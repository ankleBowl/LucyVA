import flask
import logging

app = flask.Flask(__name__)

IP_ADDRESS = "0.0.0.0"
PORT = 2000
IS_SSL = False

@app.route('/test', methods=['GET'])
def home():
    return "Hello World"

def add_route(path, function):
    path = path + "/<data>"
    # app.route(path, methods=['GET'])(function)
    app.route(path, methods=['GET'])(lambda data: function(data))

import threading

def start_web_server():
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host=IP_ADDRESS, port=PORT)

def get_server_ip():
    output = ""
    if IS_SSL:
        output += "https://"
    else:
        output += "http://"
    output += IP_ADDRESS
    output += ":"
    output += str(PORT)
    return output

thread = threading.Thread(target=start_web_server)
thread.start()