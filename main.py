from math import ceil
from utils import request

def get_tracklist(playlist_id):
    tracklist = []
    # Get initial response to work out how many songs there are in the playlist
    response = request("GET", f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=1")
    num_tracks = response["total"]
    for i in range(ceil(num_tracks/50)):  # Can only get 50 tracks at a time
        response =request("GET", f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=50&offset={i*50}")
        items = response["items"]
        for item in items:
            name = item["track"]["name"]
            artist = item["track"]["artists"][0]["name"]
            url = item["track"]["uri"]
            tracklist.append(Song(name, artist, url))
    return tracklist
