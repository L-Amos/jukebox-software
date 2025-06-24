import json
import requests

def get_secrets():
    with open("secrets.json") as f:
        secrets = json.loads(f.read())
    return secrets

def get_new_token(secrets):
    headers={"Content-Type": "application/x-www-form-urlencoded"}
    data=f"grant_type=refresh_token&refresh_token={secrets["refresh_token"]}&client_id={secrets["id"]}&client_secret={secrets["client_secret"]}"
    response = requests.post(url="https://accounts.spotify.com/api/token", data=data, headers=headers, timeout=1000)
    secrets["key"] = json.loads(response.content)["access_token"]
    # Write new key to file
    with open("secrets.json", "w") as f:
        json.dump(secrets, f)
