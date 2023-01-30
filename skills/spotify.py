from skills.skill import Skill

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from similarity import get_similarity
import threading
import os
from web_server import add_route, get_server_ip
from config import SPOTIFY_CLIENT_SECRET
from voice import say
import webbrowser
import time
import random
import requests
import base64

from transformers import AutoModelForTokenClassification, AutoTokenizer
model = AutoModelForTokenClassification.from_pretrained("ankleBowl/autotrain-lucy-song-request-1537055286")
tokenizer = AutoTokenizer.from_pretrained("ankleBowl/autotrain-lucy-song-request-1537055286")

SP_CI = '460f59d74e6349769931a57f0cacf840'
SP_URL = 'http://127.0.0.1:2000/spotify/login'
SCOPE = "user-top-read user-modify-playback-state app-remote-control streaming user-read-playback-state user-modify-playback-state"
AUTH_URL = 'https://accounts.spotify.com/api/token'

sp = None
load_run = False

class Spotify(Skill):
    def __init__(self):
        self.song_templates = [
            "I'd like to hear {song}",
            "play the album {album}",
            "I'd like to hear the album {album} by the artist named {artist}",
            "can you please play the band named {artist}",
            "play the album called {album} by the artist named {artist}",
            "play the song called {song} by the band called {artist} from {album}",
            "I'd like to hear the album called {album} by {artist}",
            "can you please play the album {album} by the artist named {artist}",
            "I'd like to hear the band named {artist}",
            "can you please play {song} by the artist named {artist} from the album {album}",
            "I'd like to hear the album named {album}",
            "I'd like to hear the song {song} from {album}",
            "play the artist {artist}",
            "can you please play the artist named {artist}",
            "I'd like to hear the artist called {artist}",
            "can you please play the artist {artist}",
            "I'd like to hear {song} from the album {album}",
            "can you please play the song called {song} by {artist}",
            "can you please play the song called {song}",
            "play the song {song}",
            "play {song} by {artist}",
            "play the song {song} by {artist}",
            "play the song {song} from the album {album}",
            "play {song}",
        ]
        super().__init__("Spotify")

    def load(self):
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
            return "I'm sorry... but I couldn't connect to Spotify. You'll need to go to my IP address, slash spotify, slash login, if you want to reconnect"

        try:
            self.get_new_token()
        except:
            return "I'm sorry... but I couldn't connect to Spotify. You'll need to go to my IP address, slash spotify, slash login, if you want to reconnect"

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
        print(r)
        self.token = r["access_token"]

        sp = spotipy.Spotify(auth=self.token)
        sp.current_user()
        self.log("OAuth login successful")

    def handle_signin(self, data):
        if "token" in data:
            token = data.split("-seperator-")[1]
            token = token.split("=")[1]
            os.remove("skills/spotify/token.txt")
            with open("skills/spotify/token.txt", "w") as f:
                f.write(token)
            self.load()
            say("You should be all good to go now. I've connected to Spotify.")
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

    def get_similarity(self, userInput):
        possibly_requested_song, possibly_requested_album, possibly_requested_artist = self.extract_song_info(userInput)

        if possibly_requested_song == "" and possibly_requested_album == "" and possibly_requested_artist == "":
            return 0

        phrases = []
        for song_template in self.song_templates:
            song_template.replace("{song}", possibly_requested_song)
            song_template.replace("{album}", possibly_requested_album)
            song_template.replace("{artist}", possibly_requested_artist)
            phrases.append(song_template)

        highestSimilarity = 0
        for phrase in phrases:
            similarity = get_similarity(userInput, phrase)
            if similarity > highestSimilarity:
                highestSimilarity = similarity
        return highestSimilarity

    def run(self, userIn):
        song_name, album_name, artist_name = self.extract_song_info(userIn)
        self.log("Heard: " + song_name + " by " + artist_name + " from " + album_name)

        songstoplay = []

        if song_name == "" and album_name == "" and artist_name != "":
            self.log("Searching for artist")
            results = sp.search(q='artist:' + artist_name, type='track', limit=10)
            true_artist = ""
            true_artist_similarity = 0
            for idx, track in enumerate(results['tracks']['items']):
                found_artist = track['artists'][0]['name']
                similarity = get_similarity(artist_name, found_artist)
                if similarity > true_artist_similarity:
                    true_artist_similarity = similarity
                    true_artist = found_artist
            self.log("Found artist: " + true_artist)
            results = sp.search(q='artist:' + true_artist, type='track', limit=10)
            for idx, track in enumerate(results['tracks']['items']):
                if track['artists'][0]['name'] == true_artist:
                    self.log("Adding song: " + track['name'] + " by " + track['artists'][0]['name'])
                    songstoplay.append({"name": track['name'], "artist": track['artists'][0]['name'], "album": track['album']['name'], "uri": track['uri']})
        elif song_name == "" and album_name != "":
            self.log("Searching for album")
            searchquery = 'album:' + album_name
            if (artist_name != ""):
                searchquery += ' artist:' + artist_name
            results = sp.search(q=searchquery, type='track', limit=10)
            true_album = ""
            true_album_similarity = 0
            for idx, track in enumerate(results['tracks']['items']):
                found_album = track['album']['name']
                similarity = get_similarity(album_name, found_album)
                if similarity > true_album_similarity:
                    true_album_similarity = similarity
                    true_album = found_album
            self.log("Found album: " + true_album)
            results = sp.search(q='album:' + true_album, type='track', limit=20)
            for idx, track in enumerate(results['tracks']['items']):
                if track['album']['name'] == true_album:
                    self.log("Adding song: " + track['name'] + " by " + track['artists'][0]['name'])
                    songstoplay.append({"name": track['name'], "artist": track['artists'][0]['name'], "album": track['album']['name'], "uri": track['uri']})
        elif song_name != "":
            self.log("Searching for song")
            searchquery = song_name
            if (artist_name != ""):
                searchquery += ' ' + artist_name
            results = sp.search(q=searchquery, type='track', limit=10)
            true_song = ""
            true_song_similarity = 0
            userquery = song_name
            if (artist_name != ""):
                userquery += ' by ' + artist_name
            if (album_name != ""):
                userquery += ' from ' + album_name
            for idx, track in enumerate(results['tracks']['items']):
                found_song = track['name']
                found_artist = track['artists'][0]['name']
                found_album = track['album']['name']
                similarityquery = found_song
                if (artist_name != ""):
                    similarityquery += " by " + found_artist
                if (album_name != ""):
                    similarityquery += " from " + found_album
                similarity = get_similarity(userquery, similarityquery)
                self.log("Comparing: " + userquery + " | " + similarityquery + " - " + str(similarity))
                if similarity > true_song_similarity:
                    true_song_similarity = similarity
                    true_song = {"name": track['name'], "artist": track['artists'][0]['name'], "album": track['album']['name'], "uri": track['uri']}
            self.log("Found song: " + str(true_song))
            if true_song != "":
                songstoplay.append(true_song)
        else:
            self.log("Sorry, I couldn't find anything to play.")
            return
        
        # play all the songs in songstoplay list
        if len(songstoplay) > 0:
            urls = []
            for song in songstoplay:
                urls.append(song['uri'])
            try:
                if sp.devices()['devices'] == []:
                    path = os.path.dirname(os.path.abspath(__file__))
                    index = os.path.join(path, 'spotify/index.html')
                    index_new = os.path.join(path, 'spotify/index-new.html')

                    html = ""
                    with open(index, 'r') as f:
                        html = f.read().replace('(TOKEN)', self.token)
                    with open(index_new, 'w') as f:
                        f.write(html)

                    webbrowser.open('file://' + index_new, new=2)

                    return "I'm sorry, I couldn't find any devices to play on."
                sp.start_playback(uris=urls)
            except spotipy.client.SpotifyException:
                self.get_new_token()

                if sp.devices()['devices'] == []:
                    return "I'm sorry, I couldn't find any devices to play on."
                sp.start_playback(uris=urls)

            if (len(songstoplay) == 1):
                return "Playing " + songstoplay[0]["name"] + " by " + songstoplay[0]["artist"]
            else:
                return "Playing " + str(len(songstoplay)) + " songs, starting with " + songstoplay[0]["name"] + " by " + songstoplay[0]["artist"]
        else:
            return "I'm sorry, I couldn't find anything to play."

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
