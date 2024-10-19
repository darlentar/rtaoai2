from rtaoai2.ui.consumer import EventConsumer

import pytest


class OpenAIEventProducerSpy:
    def __init__(self):
        self.calls = []

    async def make_audio(self, audio: str):
        self.calls.append(("make_audio", audio))

    async def make_audio_commit(self):
        self.calls.append(("make_audio_commit", ""))

    async def make_response_create(self, tools):
        self.calls.append(("make_response_create", tools))


@pytest.mark.asyncio
async def test_consumer_on_audio():
    spy = OpenAIEventProducerSpy()
    event_consumer = EventConsumer(spy)
    await event_consumer.on_audio("012390293")
    assert spy.calls == [
        ("make_audio", "012390293"),
        ("make_audio_commit", ""),
    ]


@pytest.mark.asyncio
async def test_consumer_on_response_requested():
    spy = OpenAIEventProducerSpy()
    event_consumer = EventConsumer(spy)
    await event_consumer.on_response_create(tools=[])
    assert spy.calls == [
        ("make_response_create", []),
    ]
