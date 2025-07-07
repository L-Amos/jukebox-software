"""Utility functions for the jukebox software. 

Includes a wrapper for the python requests module which automatically adds api credentials 
and generates a new api key if the old one has expired.

Also responsible for reading the user-provided config data (e.g playlist ID).
"""

import os
import requests
import json
import yaml

# Request type variables
TYPES = {
    "GET": lambda url,headers,data,timeout : requests.get(url=url,headers=headers,data=data,timeout=timeout),
    "POST": lambda url,headers,data,timeout : requests.post(url=url,headers=headers,data=data,timeout=timeout),
    "PUT": lambda url,headers,data,timeout : requests.put(url=url,headers=headers,data=data,timeout=timeout)
}

# Reading config vars
with open("../config.yaml") as f:
    config = yaml.safe_load(f)
    # Error handling
    if not config["client_id"]:
        raise KeyError("config file does not have a client id.")
    elif not config["client_secret"]:
        raise KeyError("config file does not have a client secret.")
DEVICE_ID = config["device_id"]
SONGS_PER_PAGE = config["songs_per_page"]
PLAYLIST_ID = config["playlist_id"]

def get_secrets(filepath : str) -> dict:
    """Retrieves secrets (api key and refresh token) from given file.

    :param filepath: location of secrets file (usually secrets.json)
    :type filepath: str
    :raises KeyError: if the secrets file does not contain a refresh token
    :return: the secrets as a dictionary
    :rtype: dict
    """
    if not os.path.exists(filepath):
        get_api_credentials(filepath)
    with open(filepath) as f:
        secrets = json.load(f)
    if "refresh_token" not in secrets.keys() or "access_token" not in secrets.keys():
        get_api_credentials(filepath)
        get_secrets(filepath)
    return secrets

def get_new_token(secrets: dict, filepath: str) -> dict:
    """Retrieves a new api key using a given refresh token, and writes
    to desired secrets file.

    :param secrets: existing secrets dictionary obtained from existing secrets file
    :type secrets: dict
    :param filepath: location of secrets file to write new api key to
    :type filepath: str
    :return: new secrets dictionary with new api key
    :rtype: dict
    """
    headers={"Content-Type": "application/x-www-form-urlencoded"}
    data=f"grant_type=refresh_token&refresh_token={secrets["refresh_token"]}&client_id={config["client_id"]}&client_secret={config["client_secret"]}"
    response = requests.post(url="https://accounts.spotify.com/api/token", data=data, headers=headers, timeout=1000)
    secrets["access_token"] = json.loads(response.content)["access_token"]
    # Write new key to file
    with open(filepath, "w") as f:
        json.dump(secrets, f)
    return secrets

def request(request_type: str, url: str, secrets_file: str = "../src/secrets.json", headers: dict = None, data: str = None, timeout: int = 10) -> dict:
    """Wrapper for the python requests module which automatically incorporates api credentials into the http request. 
    
    Automatically obtains new api key if the current one has expired.

    Can be used to make 3 types of http request: GET, POST and PUT.


    :param request_type: type of http request to make (GET, POST or PUT)
    :type request_type: str
    :param url: url to request
    :type url: str
    :param secrets_file: location of secrets file, defaults to "../src/secrets.json"
    :type secrets_file: str, optional
    :param headers: any headers required for the http request (EXCLUDING authorization header), defaults to {}
    :type headers: dict, optional
    :param data: any data required for the http request, defaults to None
    :type data: str, optional
    :param timeout: how long to wait (in s) for response before giving up, defaults to 1000
    :type timeout: int, optional
    :raises ValueError: if an invalid request type is parsed
    :raises ConnectionAbortedError: if the response is an error message
    :return: the json response
    :rtype: dict
    """
    if request_type not in TYPES:
        raise ValueError("invalid request type.")
    if not headers:
        headers = {}
    secrets = get_secrets(secrets_file)
    failure = True
    while failure:
        headers["Authorization"] = "Bearer "+ secrets['access_token']
        response = TYPES[request_type](url, headers, data, timeout)
        try:
            json_response = json.loads(response.content)
        except json.decoder.JSONDecodeError:
            return ''
        if 'error' in json_response.keys():
            if json_response['error']['message'] == 'The access token expired':
                secrets = get_new_token(secrets, secrets_file)
            else:
                raise ConnectionAbortedError(json_response)
        else:
            failure = False
    return json_response

def get_api_credentials(filepath : str):
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth, CacheFileHandler

    scope = "playlist-read-private playlist-read-collaborative user-modify-playback-state"

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(cache_handler=CacheFileHandler(cache_path=filepath), client_id=config["client_id"], client_secret=config["client_secret"], redirect_uri="http://127.0.0.1:4321", scope=scope))
    sp.current_user_playlists()  # Needed to actually obtain the api credentials
