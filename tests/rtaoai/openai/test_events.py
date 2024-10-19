import pytest

from rtaoai2.openai.events import (
    Event,
)


@pytest.mark.parametrize(
    "event,cls", [(cls.name, cls) for cls in Event.__subclasses__()]
)
def test_respose_audio_delta_event(event, cls, events_json):
    events_json = events_json(event)
    for j in events_json:
        assert cls.model_validate(j)
