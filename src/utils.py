import requests
import json
import yaml

TYPES = {
    "GET": lambda url,headers,data,timeout : requests.get(url=url,headers=headers,data=data,timeout=timeout),
    "POST": lambda url,headers,data,timeout : requests.post(url=url,headers=headers,data=data,timeout=timeout),
    "PUT": lambda url,headers,data,timeout : requests.put(url=url,headers=headers,data=data,timeout=timeout)
}

# Reading config vars
with open("../config.yaml") as f:
    config = yaml.safe_load(f)
    # Error handling
    if"client_id" not in config.keys():
        raise KeyError("config file does not have a client id.")
    elif "client_secret" not in config.keys():
        raise KeyError("config file does not have a client secret.")
DEVICE_ID = config["device_id"]
SONGS_PER_PAGE = config["songs_per_page"]
PLAYLIST_ID = config["playlist_id"]


def get_secrets(filepath):
    with open(filepath) as f:
        secrets = json.load(f)
    if "refresh_token" not in secrets.keys():
        raise KeyError("secrets file does not have a refresh token.")
    elif "key" not in secrets.keys():
         secrets = get_new_token(secrets, filepath)
    return secrets

def get_new_token(secrets, filepath):
   
    headers={"Content-Type": "application/x-www-form-urlencoded"}
    data=f"grant_type=refresh_token&refresh_token={secrets["refresh_token"]}&client_id={config["client_id"]}&client_secret={config["client_secret"]}"
    response = requests.post(url="https://accounts.spotify.com/api/token", data=data, headers=headers, timeout=1000)
    secrets["key"] = json.loads(response.content)["access_token"]
    # Write new key to file
    with open(filepath, "w") as f:
        yaml.dump(secrets, f)
    return secrets

def request(request_type, url, secrets_file="../src/secrets.json", headers={}, data=None, timeout=1000):
    if request_type not in TYPES:
        raise ValueError("invalid request type.")
    secrets = get_secrets(secrets_file)
    failure = True
    while failure:
        headers["Authorization"] = "Bearer "+ secrets['key']
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