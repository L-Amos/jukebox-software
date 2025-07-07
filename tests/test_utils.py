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
    assert utils.get_secrets(".pyc")

def test_request():
    with open("fixtures/fake_secrets.json") as f:  # Includes OUTDATED KEY
        fake_secrets = json.loads(f.read())
    with open(".pyc", "w") as f:  # Writing to tmp file to protect fake_secrets.json
        json.dump(fake_secrets, f)
    response = utils.request("GET", "https://api.spotify.com/v1/users/gsi6dp1hadnzqy5i3nv15rq37", secrets_file=".pyc")
    expected_response ={"display_name": "JodbyBerundi","external_urls": {"spotify": "https://open.spotify.com/user/gsi6dp1hadnzqy5i3nv15rq37"},"followers": {"href": None,"total": 1},"href": "https://api.spotify.com/v1/users/gsi6dp1hadnzqy5i3nv15rq37","id": "gsi6dp1hadnzqy5i3nv15rq37","images": [],"type": "user","uri": "spotify:user:gsi6dp1hadnzqy5i3nv15rq37"}
    assert response==expected_response
    # Check a new key was definitely generated
    with open(".pyc", "r") as f:  # Writing to tmp file to protect fake_secrets.json
        new_secrets = json.loads(f.read())
    assert fake_secrets["access_token"] != new_secrets["access_token"]
    # Checking type error
    with pytest.raises(ValueError, match="invalid request type."):
        assert utils.request("NOT_GET", "https://api.spotify.com/v1/artists/0TnOYISbd1XYRBk9myaseg", secrets_file=".pyc")

