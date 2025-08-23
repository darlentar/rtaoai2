from typing import Any


class EventConsumer:
    def __init__(self, openai_session):
        self.openai_session = openai_session

    async def on_audio(self, audio: str):
        await self.openai_session.input_audio_buffer.append(audio=audio)
        await self.openai_session.input_audio_buffer.commit()

    async def on_response_create(self, tools: list[Any]):
        await self.openai_session.response.create(tools=tools)
