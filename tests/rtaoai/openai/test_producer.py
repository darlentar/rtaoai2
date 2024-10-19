from typing import Any
import json

import pytest

from rtaoai2.openai.producer import (
    OpenAIEventProducer,
    make_audio,
    make_audio_commit,
    make_response_create,
    make_session_update,
)


class WebSocketSpy:
    def __init__(self):
        self.calls = []

    async def send(self, j: Any):
        self.calls.append(("send", j))


def test_producer_make_audio():
    assert make_audio("12345") == {
        "type": "input_audio_buffer.append",
        "audio": "12345",
    }


def test_producer_make_audio_commit():
    assert make_audio_commit() == {"type": "input_audio_buffer.commit"}


def test_producer_make_response():
    def calculate_sum(a: float, b: float) -> float:
        """Calculates the sum of two numbers."""
        return a + b

    assert make_response_create(tools=[calculate_sum]) == {
        "type": "response.create",
        "response": {
            "tools": [
                {
                    "type": "function",
                    "name": "calculate_sum",
                    "description": "Calculates the sum of two numbers.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number"},
                            "b": {"type": "number"},
                        },
                        "required": ["a", "b"],
                    },
                }
            ]
        },
    }


def test_producer_make_session_update():
    def calculate_sum(a: float, b: float) -> float:
        """Calculates the sum of two numbers."""
        return a + b

    assert make_session_update(tools=[calculate_sum]) == {
        "type": "session.update",
        "session": {
            "input_audio_transcription": {"model": "whisper-1"},
            "tools": [
                {
                    "type": "function",
                    "name": "calculate_sum",
                    "description": "Calculates the sum of two numbers.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number"},
                            "b": {"type": "number"},
                        },
                        "required": ["a", "b"],
                    },
                }
            ],
        },
    }


@pytest.mark.asyncio
async def test_openai_event_producer():
    spy = WebSocketSpy()
    openai_event_producer = OpenAIEventProducer(spy)

    await openai_event_producer.make_session_update(tools=[])
    await openai_event_producer.make_audio("1234")
    await openai_event_producer.make_audio_commit()
    await openai_event_producer.make_response_create(tools=[])

    assert spy.calls == [
        ("send", json.dumps(make_session_update(tools=[]))),
        ("send", json.dumps(make_audio("1234"))),
        ("send", json.dumps(make_audio_commit())),
        ("send", json.dumps(make_response_create(tools=[]))),
    ]
