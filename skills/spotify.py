from skills.skill import Skill

import spotipy
from similarity import get_similarity
import os
from web_server import add_route, get_server_ip
from socket_server import send_message
from config import SPOTIFY_CLIENT_SECRET
from voice import say_in_queue
import time
import requests
import base64

from config import FLASK_SERVER_PORT

from selenium import webdriver
from selenium.webdriver.common.by import By

from transformers import AutoModelForTokenClassification, AutoTokenizer
model = AutoModelForTokenClassification.from_pretrained("ankleBowl/autotrain-lucy-song-request-1537055286")
tokenizer = AutoTokenizer.from_pretrained("ankleBowl/autotrain-lucy-song-request-1537055286")

SP_CI = '460f59d74e6349769931a57f0cacf840'
SP_URL = 'http://127.0.0.1:2000/spotify/login'
SCOPE = "user-top-read user-modify-playback-state app-remote-control streaming user-read-playback-state user-modify-playback-state user-read-email user-read-private user-library-read"
AUTH_URL = 'https://accounts.spotify.com/api/token'

sp = None
load_run = False

class Spotify(Skill):
    def __init__(self):
        super().__init__("Spotify")

    def load(self):
        self.driver = None

        global load_run

        if not load_run:
            add_route("/spotify", self.handle_signin)
        load_run = True
                
        global sp

        self.refresh_token = ""
        if not os.path.exists("skills/spotify/token.txt"):
            with open("skills/spotify/token.txt", "w") as f:
                f.write("")

        with open("skills/spotify/token.txt", "r") as f:
            self.refresh_token = f.read()

        if self.refresh_token == "":
            say_in_queue("I'm sorry... but I couldn't connect to Spotify. You'll need to go to my IP address, slash spotify, slash login, if you want to reconnect")

        try:
            self.get_new_token()
        except Exception as e:
            return "I'm sorry... but I couldn't connect to Spotify. You'll need to go to my IP address, slash spotify, slash login, if you want to reconnect"
        
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(options=options)

    def voice_activity_detected(self):
        send_message("spotify,volume=0.25")

    def voice_activity_ended(self):
        send_message("spotify,volume=1")

    def get_new_token(self):
        global sp

        data = {
            "grant_type": 'refresh_token',
            "refresh_token": self.refresh_token,
        }

        url_encoded = ""
        for key in data:
            url_encoded += key + "=" + data[key] + "&"
        url_encoded = url_encoded[:-1]

        client_and_secret = SP_CI + ":" + SPOTIFY_CLIENT_SECRET
        client_and_secret = client_and_secret.encode("ascii")
        client_and_secret = base64.b64encode(client_and_secret)
        client_and_secret = client_and_secret.decode("ascii")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + client_and_secret
        }

        r = requests.post(AUTH_URL, data=url_encoded, headers=headers)
        r = r.json()
        self.token = r["access_token"]

        sp = spotipy.Spotify(auth=self.token)
        sp.current_user()

        self.liked_songs = LikedSongs()
        self.liked_songs.add_all_songs(sp)

        self.log("OAuth login successful")

    def handle_signin(self, data):
        if data == "web_player_loaded":
            self.player_loaded = True
            return "Success"
        if data == "web_player_ready":
            self.player_ready = True
            return "Success"
        if data == "web_player":
            path = os.path.dirname(os.path.abspath(__file__))
            index = os.path.join(path, 'spotify/index.html')
            index_new = os.path.join(path, 'spotify/index-new.html')

            html = ""
            if os.path.exists(index_new):
                os.remove(index_new)
            with open(index, 'r') as f:
                html = f.read().replace('(TOKEN)', self.token)
            return html
        if "token" in data:
            token = data.split("-seperator-")[1]
            token = token.split("=")[1]
            os.remove("skills/spotify/token.txt")
            with open("skills/spotify/token.txt", "w") as f:
                f.write(token)
            self.load()
            say_in_queue("You should be all good to go now. I've connected to Spotify.")
            return "You can close this window now."
        else:
            url_to_direct_to = "https://accounts.spotify.com/authorize"
            url_to_direct_to += "?client_id=" + SP_CI
            url_to_direct_to += "&response_type=code"
            url_to_direct_to += "&redirect_uri=" + SP_URL
            url_to_direct_to += "&scope=" + SCOPE
            url_to_direct_to += "&show_dialog=true"

            login_page = ""
            with open("skills/spotify/login.html", "r") as f:
                login_page = f.read()
            login_page = login_page.replace("(URL)", url_to_direct_to)
            login_page = login_page.replace("(SITE_URL)", get_server_ip())
            login_page = login_page.replace("(REDIR_URL)", SP_URL)
            login_page = login_page.replace("(CLIENT_ID)", SP_CI)
            login_page = login_page.replace("(SPOTIFY_SECRET)", SPOTIFY_CLIENT_SECRET)

            return login_page

    def run(self, userIn):
        song_name, album_name, artist_name = self.extract_song_info(userIn)
        self.log("Heard: " + song_name + " by " + artist_name + " from " + album_name)

        songstoplay = []

        if song_name != "" and artist_name != "":
            query = song_name + " by " + artist_name
            query = query.lower();
        elif song_name != "":
            query = song_name
            query = query.lower();
        else:
            query = "THIS IS NOT PRESENT IN THE LIBRARY BECAUSE IT IS NOT A SONG"
        song = self.liked_songs.get_song(query)
        if song is not None:
            songstoplay.append(self.spotify_song_to_dict(song))
        else:
            self.log("Song not found in library, reverting to Spotify search")
            if song_name != "":
                self.log("Searching for song")
                query = song_name
                if artist_name != "":
                    query += " by " + artist_name
                if album_name != "":
                    query += " from " + album_name
                results = self.try_search(query, "track", 4)
                song = results['tracks']['items'][0]
                songstoplay.append(self.spotify_song_to_dict(song))
            elif album_name != "":
                self.log("Searching for album")
                query = album_name
                if artist_name != "":
                    query += " by " + artist_name
                results = self.try_search(query, "album", 4)
                album = results['albums']['items'][0]
                uri = album['uri']
                album = sp.album(uri)
                for track in album['tracks']['items']:
                    track['album'] = {}
                    track['album']['name'] = album_name
                    songstoplay.append(self.spotify_song_to_dict(track))
            elif artist_name != "":
                self.log("Searching for artist")
                query = artist_name
                results = self.try_search(query, "artist", 4)
                artist = results['artists']['items'][0]
                uri = artist['uri']
                artist = sp.artist_top_tracks(uri)
                for track in artist['tracks']:
                    songstoplay.append(self.spotify_song_to_dict(track))
        
        if len(songstoplay) > 0:
            urls = []
            for song in songstoplay:
                urls.append(song['uri'])
            # if (len(songstoplay) == 1):
            #     say_in_queue("Playing " + songstoplay[0]["name"] + " by " + songstoplay[0]["artist"])
            # else:
            #     say_in_queue("Playing " + str(len(songstoplay)) + " songs, starting with " + songstoplay[0]["name"] + " by " + songstoplay[0]["artist"])
            self.try_play_songs(urls)
        else:
            say_in_queue("I'm sorry, I couldn't find anything to play.")
        
    def try_search(self, query, type, limit):
        try:
            return sp.search(q=query, type=type, limit=limit)
        except spotipy.client.SpotifyException as error:
            self.log("Refreshing token")
            self.get_new_token()
            return self.try_search(query, type, limit)
        
    def try_play_songs(self, urls):
        try: 
            sp.start_playback(uris=urls)
        except spotipy.client.SpotifyException as error:
            self.log("Couldn't play songs")
            error = error.reason
            if error == "NO_ACTIVE_DEVICE":
                if sp.devices()['devices'] == []:
                    self.log("Launching player")
                    self.launch_player()
                sp.transfer_playback(sp.devices()['devices'][0]['id'])
                self.log("Retrying play songs")
                self.try_play_songs(urls)
            else:
                self.log("Refreshing token")
                self.get_new_token()
                self.launch_player()
                self.log("Launching player")
                self.try_play_songs(urls)


    def launch_player(self):
        self.player_ready = False
        self.player_loaded = False

        self.driver.get('http://127.0.0.1:' + str(FLASK_SERVER_PORT) + '/spotify/web_player')
        while not self.player_loaded:
            # self.log("Waiting for player to load")
            time.sleep(0.1)
        self.driver.find_element(By.ID, "play").click()
        while not self.player_ready:
            # self.log("Waiting for player to be ready")
            time.sleep(0.1)
        time.sleep(0.5)


    def extract_song_info(self, userIn):
        inputs = tokenizer(userIn, return_tensors="pt")
        outputs = model(**inputs)
        
        labels = outputs.logits.argmax(2)[0].tolist()
        tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0].tolist())
        song = ""
        artist = ""
        album = ""
        for token, label in zip(tokens, labels):
            if token == "[CLS]" or token == "[SEP]":
                continue
            if label == 3:
                if token.startswith("##"):
                    song += token[2:]
                else:
                    song += " " + token
            elif label == 1:
                if token.startswith("##"):
                    artist += token[2:]
                else:
                    artist += " " + token
            elif label == 0:
                if token.startswith("##"):
                    album += token[2:]
                else:
                    album += " " + token
        return song.strip(), album.strip(), artist.strip()
    
    def spotify_song_to_dict(self, song):
        return {"name": song['name'], "artist": song['artists'][0]['name'], "album": song['album']['name'], "uri": song['uri']}

import json
import regex as re

class LikedSongs:
    def __init__(self):
        self.name_to_uri = {}
        self.name_and_artist_to_uri = {}
        self.song_uri_to_song = {}

        self.read_in_songs()

    def add_song(self, song):
        name = song['name'].lower()
        name.replace(" u ", " you ")
        name.replace(" ur ", " your ")
        name.replace(" 2 ", " to ")
        in_paren = False
        output = ""
        for x in range(len(name)):
            if name[x] == '(':
                in_paren = True
            elif name[x] == ')':
                in_paren = False
            elif not in_paren:
                output += name[x]
        name = output
        name = re.sub(r'\W+', '', name)
        artist = song['artists'][0]['name'].lower()
        artist = re.sub(r'\W+', '', artist)

        # print(name + " by " + artist + " - " + song['uri'])

        self.name_to_uri[name] = song['uri']
        self.name_and_artist_to_uri[name + "by" + artist] = song['uri']
        self.song_uri_to_song[song['uri']] = song

    def add_all_songs(self, sp):
        found_spot = False;
        x = 0
        while not found_spot:
            results = sp.current_user_saved_tracks(limit=50, offset=x)
            for idx, item in enumerate(results['items']):
                if self.has_song(item['track']['uri']):
                    found_spot = True
                    break
                track = item['track']
                self.add_song(track)
                print("[SPOTIFY] Added song: " + track['name'] + " by " + track['artists'][0]['name']) 
            x += 50
            if len(results['items']) < 50:
                found_spot = True
        self.write_out_songs()

    def get_song(self, name):
        name = name.lower()
        name.replace(" u ", " you ")
        name.replace(" ur ", " your ")
        name.replace(" 2 ", " to ")
        name = re.sub(r'\W+', '', name)
        if name in self.name_to_uri:
            return self.song_uri_to_song[self.name_to_uri[name]]
        elif name in self.name_and_artist_to_uri:
            return self.song_uri_to_song[self.name_and_artist_to_uri[name]]
        else:
            return None
        
    def write_out_songs(self):
        with open('skills/spotify/songs.json', 'w') as outfile:
            json.dump(self.song_uri_to_song, outfile)

    def read_in_songs(self):
        if not os.path.exists('skills/spotify/songs.json'):
            return
        with open('skills/spotify/songs.json') as json_file:
            self.song_uri_to_song = json.load(json_file)
            for song in self.song_uri_to_song.values():
                self.add_song(song)

    def has_song(self, uri):
        return uri in self.song_uri_to_song