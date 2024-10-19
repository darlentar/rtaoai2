import os
import pathlib
import json

import pytest


@pytest.fixture
def events_json():
    def _events_json(event):
        events_json = []
        for file in os.listdir("dumps"):
            if event == "." or event in file:
                with open(pathlib.Path.cwd().resolve() / "dumps" / file) as f:
                    events_json.append((file, json.load(fp=f)))
        events_json = sorted(events_json, key=lambda k: k[0])  # sorted by name so time
        return [e[1] for e in events_json]

    return _events_json
