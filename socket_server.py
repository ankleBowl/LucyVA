from websocket_server import WebsocketServer
from config import SOCKET_SERVER_PORT
import threading

skill_to_function = {}

# Called for every client connecting (after handshake)
def new_client(client, server):
	print("New client connected and was given id %d" % client['id'])

# Called for every client disconnecting
def client_left(client, server):
	print("Client(%d) disconnected" % client['id'])

# Called when a client sends a message
def message_received(client, server, message):
	message_parts = message.split(".")
	skill = message_parts[0]
	data = message_parts[1]
	if skill in skill_to_function:
		skill_to_function[skill](data)
	
def register_new_skill(skill, function):
	skill_to_function[skill] = function

def send_message(message):
	global server
	server.send_message_to_all(message)

def start_socket_server():
    global server
    server = WebsocketServer(port=SOCKET_SERVER_PORT)
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    server.run_forever()

thread = threading.Thread(target=start_socket_server)
thread.start()