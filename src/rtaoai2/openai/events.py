from typing import ClassVar
from pydantic import BaseModel


class Event(BaseModel):
    @property
    def name(self):
        raise NotImplementedError


class ResponseAudioDeltaEvent(Event):
    name: ClassVar[str] = "response.audio.delta"
    delta: str


class ResponseAudioTranscriptDeltaEvent(Event):
    name: ClassVar[str] = "response.audio_transcript.delta"
    delta: str


class ResponseDoneEvent(Event):
    name: ClassVar[str] = "response.done"


class ResponseCreatedEvent(Event):
    name: ClassVar[str] = "response.created"


class ConversationItemInputAudioTranscriptionCompleted(Event):
    name: ClassVar[str] = "conversation.item.input_audio_transcription.completed"
    transcript: str
