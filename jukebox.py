from math import ceil
from utils import request

PLAYLIST_ID = "0bluwA0qhGV7ylBKELLFWm"
SONGS_PER_PAGE = 24
class Song:
    def __init__(self, title, artist, uri):
        self.title = title
        self.artist = artist
        self.uri = uri
    
    def play(self, device_id="01f5bffb-732b-4201-955a-1c0dfb727360_amzn_1"):
        headers = {"Content-Type": "application/json"}
        data = f'{{"uris": ["{self.uri}"],"position_ms": 0}}'
        url=f"https://api.spotify.com/v1/me/player/play?device_id={device_id}"
        request("PUT", url, headers=headers, data=data)

class Page:
    def __init__(self, playlist_id, page_num):
        self.playlist_id = playlist_id
        self.page_num = page_num
        self.tracks = get_tracks(playlist_id, (page_num)*SONGS_PER_PAGE)

    def display(self):
        print(f"PAGE {self.page_num+1}\n" + "="*len(f"PAGE {self.page_num+1}"))
        for i in range(0, len(self.tracks)):
            print(f"{i+1:02}:\t{self.tracks[i].title} - {self.tracks[i].artist}")

    def refresh(self):
        self.tracks = get_tracks(self.playlist_id, (self.page_num)*SONGS_PER_PAGE)

def get_tracks(playlist_id, offset):
    tracklist = []
    response = request("GET", f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit={SONGS_PER_PAGE}&offset={offset}")
    items = response["items"]
    for item in items:
        name = item["track"]["name"]
        artist = item["track"]["artists"][0]["name"]
        uri = item["track"]["uri"]
        tracklist.append(Song(name, artist, uri))
    return tracklist

def play_song(song_uri, device_id="01f5bffb-732b-4201-955a-1c0dfb727360_amzn_1"):
    headers = {"Content-Type": "application/json"}
    data = f'{{"uris": ["{song_uri}"],"position_ms": 0}}'
    url=f"https://api.spotify.com/v1/me/player/play?device_id={device_id}"
    request("PUT", url, headers=headers, data=data)

if __name__ == "__main__":
    num_songs = request("GET", f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID}")["tracks"]["total"]
    num_pages = ceil(num_songs/SONGS_PER_PAGE)
    pages = [Page(PLAYLIST_ID, i) for i in range(num_pages)]
    active_page = 0
    while True:
        pages[active_page].refresh()
        pages[active_page].display()
        user_input = input("\nPick A Song\n'<' To Go Back\n'>' To Go Forwards\n")
        if user_input=="q":
            break
        elif user_input == "<":
            active_page -=1
            if active_page<0:
                active_page = num_pages-1
        elif user_input==">":
            active_page += 1
            if active_page > num_pages-1:
                active_page = 0
        else:
            try:
                song_selection = int(user_input)
            except ValueError:
                print("\nERROR: ENTER A VALID SONG NUMBER.")
            else:
                if song_selection > len(pages[active_page].tracks) or song_selection <= 0:
                    print("\nERROR: ENTER A VALID SONG NUMBER.")
                else:
                    play_song(pages[active_page].tracks[song_selection-1].uri)
