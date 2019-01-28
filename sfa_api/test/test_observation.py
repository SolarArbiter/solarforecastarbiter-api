import pytest


import sfa_api
import json
from sfa_api import create_app
from sfa_api.demo import (Observation, 

VALID_JSON = {
    "extra_parameters": {
      "instrument": "Ascension Technology Rotating Shadowband Pyranometer"
    },
    "name": "Ashland OR, ghi",
    "provider": "UO SRML",
    "site_id": "123e4567-e89b-12d3-a456-426655440001",
    "variable": "ghi",
    "Value Type": "Interval Mean",
    "Interval Label": "Start"
}
INVALID_JSON = {}


def test_observation_post():
    
