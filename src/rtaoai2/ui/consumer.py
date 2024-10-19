from typing import Any


class EventConsumer:
    def __init__(self, openai_event_producer):
        self.openai_event_producer = openai_event_producer

    async def on_audio(self, audio: str):
        await self.openai_event_producer.make_audio(audio)
        await self.openai_event_producer.make_audio_commit()

    async def on_response_create(self, tools: list[Any]):
        await self.openai_event_producer.make_response_create(tools)
