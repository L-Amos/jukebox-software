import requests
import json

TYPES = {
    "GET": lambda url,headers,data,timeout : requests.get(url=url,headers=headers,data=data,timeout=timeout),
    "POST": lambda url,headers,data,timeout : requests.post(url=url,headers=headers,data=data,timeout=timeout),
    "PUT": lambda url,headers,data,timeout : requests.put(url=url,headers=headers,data=data,timeout=timeout)
}

def get_secrets(filepath):
    with open(filepath) as f:
        secrets = json.loads(f.read())
    if "key" not in secrets.keys():
        raise KeyError("secrets file does not have an access token.")
    elif "id" not in secrets.keys():
        raise KeyError("secrets file does not have a client id.")
    elif "client_secret" not in secrets.keys():
        raise KeyError("secrets file does not have a client secret.")
    elif "refresh_token" not in secrets.keys():
         raise KeyError("secrets file does not have a refresh token.")
    return secrets

def get_new_token(secrets, filepath):
    headers={"Content-Type": "application/x-www-form-urlencoded"}
    data=f"grant_type=refresh_token&refresh_token={secrets["refresh_token"]}&client_id={secrets["id"]}&client_secret={secrets["client_secret"]}"
    response = requests.post(url="https://accounts.spotify.com/api/token", data=data, headers=headers, timeout=1000)
    secrets["key"] = json.loads(response.content)["access_token"]
    # Write new key to file
    with open(filepath, "w") as f:
        json.dump(secrets, f)
    return secrets

def request(type,url, secrets_file="secrets.json", headers={}, data=None, timeout=1000):
    if type not in TYPES:
        raise ValueError("invalid request type.")
    secrets = get_secrets(secrets_file)
    failure = True
    while failure:
        headers["Authorization"] = "Bearer "+ secrets['key']
        response = TYPES[type](url, headers, data, timeout)
        json_response = json.loads(response.content)
        if 'error' in json_response.keys():
            if json_response['error']['message'] == 'The access token expired':
                secrets = get_new_token(secrets, secrets_file)
            else:
                raise ConnectionAbortedError(json_response)
        else:
            failure = False
    return json_response