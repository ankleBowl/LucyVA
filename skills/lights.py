from skills.skill import Skill
from similarity import get_similarity

from websockets import connect
import asyncio
import json
import time;
import threading
from config import HOME_ASSISTANT_IP, HOME_ASSISTANT_TOKEN

from transformers import AutoModelForTokenClassification, AutoTokenizer
model = AutoModelForTokenClassification.from_pretrained("ankleBowl/autotrain-lucy-light-control-3122788375")
tokenizer = AutoTokenizer.from_pretrained("ankleBowl/autotrain-lucy-light-control-3122788375")

class Lights(Skill):
    def __init__(self):
        self.areas = []

        self.queued_messages = []
        self.request_id = 0

        self.connected = False
        self.connectionError = False

        self.default_room = "Garage"

        super().__init__("Lights")

    def load(self):
        thread = threading.Thread(target=asyncio.run, args=(self.connect_to_server("ws://" + HOME_ASSISTANT_IP + "/api/websocket"),))
        thread.start()

        while self.connected == False and self.connectionError == False:
            time.sleep(1)
        
        if self.connectionError:
            self.log("Error connecting to HomeAssistant")
            return "There was an error connecting to HomeAssistant. Make sure the server IP and access token are correct."
        return None

    async def connect_to_server(self, url):
        try:
            websocket = await connect(url)
        except:
            self.connectionError = True
            return
        auth_recieve = await websocket.recv()
        auth = {
            "type": "auth",
            "access_token": HOME_ASSISTANT_TOKEN
        }
        await websocket.send(json.dumps(auth))
        auth_status = await websocket.recv()
        auth_status = json.loads(auth_status)
        if (auth_status["type"] != "auth_ok"):
            print("HomeAssistant authentication failed!")
            print("Error: " + auth_status["message"])
            self.connectionError = True
            return

        print("HomeAssistant authentication successful!")
        self.request_id += 1

        last_home_refresh = time.time() - 60

        while True:
            self.connected = True
            if (len(self.queued_messages) == 0):
                if (time.time() - last_home_refresh > 60):

                    await websocket.send(json.dumps({ "type": 'config/area_registry/list', "id": self.request_id }))
                    self.request_id += 1
                    area_list = await websocket.recv()
                    area_list = json.loads(area_list)

                    self.areas.clear();
                    if (area_list["success"] == True):
                        for area in area_list["result"]:
                            self.areas.append(area["name"])
                    last_home_refresh = time.time()
                    # print("Refreshed HomeAssistant data")

                await asyncio.sleep(0.25)
                continue;

            for message in self.queued_messages:
                message["id"] = self.request_id
                self.request_id += 1

                await websocket.send(json.dumps(message))
                sus = await websocket.recv()

            self.queued_messages.clear()

    def run(self, userIn):
        self.log("Heard: " + userIn)

        actual_area = None

        for area in self.areas:
            area = area.lower()
            userIn = userIn.lower()
            if area in userIn:
                actual_area = area
                break
        
        if actual_area == None:
            actual_area = self.default_room
            # self.log("Could not determine the area")
            # return "I'm sorry, I couldn't figure out what room you meant."

        should_turn_on, dim_state, dim_percent, color = self.extract_query_info(userIn)

        allowed_colors = ["red", "green", "blue", "yellow", "orange", "purple", "pink", "white", "black", "gray", "grey", "brown", "cyan", "magenta", "teal", "indigo", "violet", "maroon", "turquoise", "lime", "aqua", "chartreuse", "coral", "crimson", "fuchsia", "gold", "khaki", "lavender", "magenta", "olive", "salmon", "sienna", "tan", "thistle", "tomato", "violet", "wheat"]
        if not color in allowed_colors:
            color = ""

        self.control_lights(actual_area, should_turn_on, color, dim_percent)

        message = "Turning the " + actual_area + " lights " + ("on" if should_turn_on else "off")
        if not color == "" and not dim_percent == 100:
            message += " to " + color + " and " + str(dim_percent) + " percent brightness"
        elif not color == "":
            message += " and setting the color to " + color
        elif not dim_percent == 100:
            message += " and setting the brightness to " + str(dim_percent) + " percent"
    
        return message

    def extract_query_info(self, userIn):
        inputs = tokenizer(userIn, return_tensors="pt")
        outputs = model(**inputs)
        
        labels = outputs.logits.argmax(2)[0].tolist()
        tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0].tolist())

        outputs = [
            "", #BRI
            "", #COL
            "", #DIM
            "", #EMP
            "", #OFF
            "", #ONN
            ""  #PER
        ]

        for token, label in zip(tokens, labels):
            if token == "[CLS]" or token == "[SEP]":
                continue
            if token.startswith("##"):
                outputs[label] = outputs[label] + token[2:]
            else:
                outputs[label] = outputs[label] + " " + token

        shouldBrighten = outputs[0] != ""
        color = outputs[1].strip()
        shouldDim = outputs[2] != ""
        shouldTurnOff = outputs[4] != ""
        dimPercentage = ''.join([i for i in outputs[6] if i.isdigit()])

        willTurnOn = not shouldTurnOff
        dimState = 0
        if shouldBrighten:
            dimState = 1
        elif shouldDim:
            dimState = -1

        if dimPercentage == "":
            dimPercentage = 100
        else:
            dimPercentage = int(dimPercentage)
        
        return willTurnOn, dimState, dimPercentage, color

    def control_lights(self, area, shouldTurnOn, color, brightness):
        json_data = {
            "id": 24,
            "type": "call_service",
            "domain": "light",
            "service": "turn_on" if shouldTurnOn else "turn_off",
            "target": {
                "area_id": area
            }
        }

        if shouldTurnOn:
            json_data["service_data"] = {
                "brightness": str(brightness)
            }

            if color != "":
                json_data["service_data"]["color_name"] = color

        self.log("Sending message to HomeAssistant")

        self.queued_messages.append(json_data)