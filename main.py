from math import ceil
from utils import request

class Song:
    def __init__(self, title, artist, url):
        self.title = title
        self.artist = artist
        self.url = url

class Page:
    def __init__(self, playlist_id, page_num):
        self.page_num = page_num
        self.tracks = get_tracks(playlist_id, (page_num-1)*20)

    def display(self):
        print(f"PAGE {self.page_num}\n" + "="*len(f"PAGE {self.page_num}"))
        for i in range(0, len(self.tracks)):
            print(f"{i+1}:\t{self.tracks[i].title} - {self.tracks[i].artist}")

def get_tracks(playlist_id, offset):
    tracklist = []
    # Get initial response to work out how many songs there are in the playlist
    response = request("GET", f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=1")
    response =request("GET", f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=20&offset={offset}")
    items = response["items"]
    for item in items:
        name = item["track"]["name"]
        artist = item["track"]["artists"][0]["name"]
        url = item["track"]["uri"]
        tracklist.append(Song(name, artist, url))
    return tracklist

def play_song(song_url, device_id="01f5bffb-732b-4201-955a-1c0dfb727360_amzn_1"):
    headers = {"Content-Type": "application/json"}
    data = f'{{"uris": ["{song_url}"],"position_ms": 0}}'
    url=f"https://api.spotify.com/v1/me/player/play?device_id={device_id}"
    request("PUT", url, headers=headers, data=data)

