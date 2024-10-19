def make_audio(audio: str) -> dict[str, str]:
    return {"type": "audio", "data": audio}


def make_input_transcript(transcript: str) -> dict[str, str]:
    return {"type": "input_transcript", "data": transcript}


def make_audio_transcript(transcript: str) -> dict[str, str]:
    return {"type": "transcript", "data": transcript}


class EventProducer:
    def __init__(self, websocket):
        self.websocket = websocket

    async def on_response_audio_delta_event(self, event):
        await self.websocket.send_json(make_audio(event.delta))

    async def on_response_audio_transcript_delta_event(self, delta):
        await self.websocket.send_json(make_audio_transcript(delta))

    async def on_response_audio_input_transcript_done_event(self, transcript):
        await self.websocket.send_json(make_input_transcript(transcript))

    async def on_response_created(self, event):
        pass

    async def on_response_done(self, event):
        await self.websocket.send_json({"type": "message", "data": "response.done"})
