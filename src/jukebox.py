"""Main jukebox software.

Uses spotify web API to obtain the contents of a playlist (set in config.yaml). Presents
user with the songs of the playlist split into pages of a set length (set in config.yaml). Upon user inputting
the number of the desired song on the page, the web API is used to play the song on a chosen device (set in config.yaml).

"""

from math import ceil
if __name__=="__main__":
    from utils import request, SONGS_PER_PAGE, PLAYLIST_ID, refresh_device_id
else:
    from src.utils import request, SONGS_PER_PAGE, PLAYLIST_ID, refresh_device_id

class Song:
    """General song class.
    """
    def __init__(self, title : str, artist : str, uri : str):
        self.title = title
        self.artist = artist
        self.uri = uri
        self.device_id = refresh_device_id()

    def play(self):
        """Plays the song on a given device.
        """
        headers = {"Content-Type": "application/json"}
        data = f'{{"uris": ["{self.uri}"],"position_ms": 0}}'
        url=f"https://api.spotify.com/v1/me/player/play?device_id={self.device_id}"
        try:
            request("PUT", url, headers=headers, data=data)
        except ConnectionAbortedError as e:
            new_id = refresh_device_id()
            if self.device_id==new_id:
                print(str(e))
            else:
                self.device_id = new_id
                self.play()


class Page:
    """Class for a page of songs.
    """
    def __init__(self, playlist_id : str, page_num : int):
        self.playlist_id = playlist_id
        self.page_num = page_num
        self.refresh()

    def display(self):
        """Displays the contents of the page (ONLY IF THIS FILE IS RUN).
        """
        print(f"PAGE {self.page_num+1}\n" + "="*len(f"PAGE {self.page_num+1}"))
        for i,_ in enumerate(self.tracks):
            print(f"{i+1:02}:\t{self.tracks[i].title} - {self.tracks[i].artist}")

    def refresh(self):
        """Refreshes the page songs by querying the spotify web API.

        :param playlist_id: ID of playlist to get tracks from
        :type playlist_id: str
        :param offset: offset from the start from which to get the tracks (e.g offset of 5 will get the 6th track onwards)
        :type offset: int
        """
        self.tracks = []
        response = request("GET", f"https://api.spotify.com/v1/playlists/{self.playlist_id}/tracks?limit={SONGS_PER_PAGE}&offset={(self.page_num)*SONGS_PER_PAGE}")
        items = response["items"]
        for item in items:
            name = item["track"]["name"]
            artist = item["track"]["artists"][0]["name"]
            uri = item["track"]["uri"]
            self.tracks.append(Song(name, artist, uri))

# Basic interface for when this file is run
if __name__ == "__main__":
    num_songs = request("GET", f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID}")["tracks"]["total"]
    num_pages = ceil(num_songs/SONGS_PER_PAGE)
    pages = [Page(PLAYLIST_ID, i) for i in range(num_pages)]
    active_page = 0
    while True:
        pages[active_page].refresh()
        pages[active_page].display()
        user_input = input("\nPick A Song\n'<' To Go Back\n'>' To Go Forwards\n")
        # Parsing user input
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
                    pages[active_page].tracks[song_selection-1].play()
