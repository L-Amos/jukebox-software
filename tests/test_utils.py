# Changing path for imports
import sys
import os
import pytest
sys.path.append("../")

import json
from src import utils

def test_get_secrets():
    with open("fixtures/fake_secrets.json") as f:
        fake_secrets = json.loads(f.read())
    # Testing basic functionality
    test_secrets = utils.get_secrets("fixtures/fake_secrets.json")
    assert test_secrets==fake_secrets
    # Testing error_checking - uses .pyc file to protect contents of fake_secrets.json
    fake_secrets_refreshless = dict(fake_secrets)
    fake_secrets_refreshless.pop("refresh_token")
    with open(".pyc", "w") as f:  
        json.dump(fake_secrets_refreshless, f)
    with pytest.raises(KeyError, match="secrets file does not have a refresh token."):
        assert utils.get_secrets(".pyc")

def test_request():
    with open("fixtures/fake_secrets.json") as f:  # Includes OUTDATED KEY
        fake_secrets = json.loads(f.read())
    with open(".pyc", "w") as f:  # Writing to tmp file to protect fake_secrets.json
        json.dump(fake_secrets, f)
    response = utils.request("GET", "https://api.spotify.com/v1/artists/0TnOYISbd1XYRBk9myaseg", secrets_file=".pyc")
    expected_response = {'external_urls': {'spotify': 'https://open.spotify.com/artist/0TnOYISbd1XYRBk9myaseg'}, 'followers': {'href': None, 'total': 11669454}, 'genres': [], 'href': 'https://api.spotify.com/v1/artists/0TnOYISbd1XYRBk9myaseg', 'id': '0TnOYISbd1XYRBk9myaseg', 'images': [{'url': 'https://i.scdn.co/image/ab6761610000e5eb4051627b19277613e0e62a34', 'height': 640, 'width': 640}, {'url': 'https://i.scdn.co/image/ab676161000051744051627b19277613e0e62a34', 'height': 320, 'width': 320}, {'url': 'https://i.scdn.co/image/ab6761610000f1784051627b19277613e0e62a34', 'height': 160, 'width': 160}], 'name': 'Pitbull', 'popularity': 89, 'type': 'artist', 'uri': 'spotify:artist:0TnOYISbd1XYRBk9myaseg'}
    assert response==expected_response
    # Check a new key was definitely generated
    with open(".pyc", "r") as f:  # Writing to tmp file to protect fake_secrets.json
        new_secrets = json.loads(f.read())
    assert fake_secrets["key"] != new_secrets["key"]
    # Checking type error
    with pytest.raises(ValueError, match="invalid request type."):
        assert utils.request("NOT_GET", "https://api.spotify.com/v1/artists/0TnOYISbd1XYRBk9myaseg", secrets_file=".pyc")

