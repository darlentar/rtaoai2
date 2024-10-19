from typing import Any
from collections import namedtuple

import pytest

from rtaoai2.ui.producer import (
    make_audio,
    make_input_transcript,
    make_audio_transcript,
    EventProducer,
)


def test_ui_produder_make_audio():
    assert make_audio("12349") == {"type": "audio", "data": "12349"}


def test_ui_producer_make_input_transcript():
    assert make_input_transcript("transcript") == {
        "type": "input_transcript",
        "data": "transcript",
    }


def test_ui_producer_make_audio_transcript():
    assert make_audio_transcript("audio") == {
        "type": "transcript",
        "data": "audio",
    }


@pytest.mark.asyncio
async def test_openai_ui_bridge():
    class WebSocketSpy:
        def __init__(self):
            self.calls = []

        async def send_json(self, j: Any) -> None:
            self.calls.append(("send_json", j))

    websocket = WebSocketSpy()
    event_producer = EventProducer(websocket)
    FakeEvent = namedtuple("FakeEvent", ["delta"])
    event = FakeEvent("1234")

    await event_producer.on_response_audio_delta_event(event)
    assert websocket.calls == [("send_json", make_audio(event.delta))]

    await event_producer.on_response_audio_transcript_delta_event(event.delta)
    assert websocket.calls == [
        ("send_json", make_audio(event.delta)),
        ("send_json", make_audio_transcript(event.delta)),
    ]

    await event_producer.on_response_audio_input_transcript_done_event(event.delta)
    assert websocket.calls == [
        ("send_json", make_audio(event.delta)),
        ("send_json", make_audio_transcript(event.delta)),
        ("send_json", make_input_transcript(event.delta)),
    ]
