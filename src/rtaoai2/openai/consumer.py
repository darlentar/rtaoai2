from enum import Enum
from typing import Any

from .events import (
    Event,
    ResponseAudioDeltaEvent,
    ResponseAudioTranscriptDeltaEvent,
    ResponseDoneEvent,
    ResponseCreatedEvent,
    ConversationItemInputAudioTranscriptionCompleted,
)


class UnknownEventError(Exception):
    pass


class OpenAIEventConsumer:
    def __init__(self, processed_events: list[type[Event]] | None = None):
        if processed_events is None:
            processed_events = Event.__subclasses__()
        self.events_from_json = {}
        for processed_event in processed_events:
            self.events_from_json[processed_event.name] = processed_event.model_validate

    def process_event(self, event: Any) -> Event:
        try:
            return self.events_from_json[event["type"]](event)
        except KeyError:
            raise UnknownEventError


class ResponseState(Enum):
    WAITING_AUDIO_INPUT_TRANSCRIPTION = 0
    WAITING_RESPONSE_DONE = 1


class OpenAIWaitInputTranscriptEventConsumer:
    def __init__(self, event_consumer, response_producer):
        self.event_consumer = event_consumer
        self.response_producer = response_producer
        self.process_event_state = ResponseState.WAITING_AUDIO_INPUT_TRANSCRIPTION
        self.response_audio_transcript_queue = ""

    async def on_event(self, event):
        try:
            event = self.event_consumer.process_event(event)
        except UnknownEventError:
            event = None
        if isinstance(event, ResponseAudioDeltaEvent):
            await self.response_producer.on_response_audio_delta_event(event)
        elif isinstance(event, ResponseAudioTranscriptDeltaEvent):
            if (
                self.process_event_state
                is ResponseState.WAITING_AUDIO_INPUT_TRANSCRIPTION
            ):
                self.response_audio_transcript_queue += event.delta
            else:
                if self.response_audio_transcript_queue:
                    await (
                        self.response_producer.on_response_audio_transcript_delta_event(
                            self.response_audio_transcript_queue + event.delta
                        )
                    )
                    self.response_audio_transcript_queue = ""
                elif event.delta != "":
                    await (
                        self.response_producer.on_response_audio_transcript_delta_event(
                            event.delta
                        )
                    )

        elif isinstance(event, ResponseDoneEvent):
            if self.response_audio_transcript_queue:
                await self.response_producer.on_response_audio_transcript_delta_event(
                    event
                )
                self.response_audio_transcript_queue = ""
            await self.response_producer.on_response_done(event)
            self.process_event_state = ResponseState.WAITING_AUDIO_INPUT_TRANSCRIPTION
        elif isinstance(event, ResponseCreatedEvent):
            await self.response_producer.on_response_created(event)
        elif isinstance(event, ConversationItemInputAudioTranscriptionCompleted):
            await self.response_producer.on_response_audio_input_transcript_done_event(
                event.transcript
            )
            if self.response_audio_transcript_queue:
                await self.response_producer.on_response_audio_transcript_delta_event(
                    self.response_audio_transcript_queue
                )
                self.response_audio_transcript_queue = ""
            self.process_event_state = ResponseState.WAITING_RESPONSE_DONE


class OpenAIStreamingEventConsummer:
    def __init__(self, event_consummer, response_producer):
        self.event_consummer = event_consummer
        self.response_producer = response_producer

    async def on_event(self, event):
        try:
            event = self.event_consummer.process_event(event)
        except UnknownEventError:
            event = None
        if isinstance(event, ResponseAudioDeltaEvent):
            await self.response_producer.on_response_audio_delta_event(event)
        elif isinstance(event, ResponseAudioTranscriptDeltaEvent):
            if event.delta != "":
                await self.response_producer.on_response_audio_transcript_delta_event(
                    event.delta
                )

        elif isinstance(event, ResponseDoneEvent):
            await self.response_producer.on_response_done(event)
        elif isinstance(event, ResponseCreatedEvent):
            await self.response_producer.on_response_created(event)
        elif isinstance(event, ConversationItemInputAudioTranscriptionCompleted):
            await self.response_producer.on_response_audio_input_transcript_done_event(
                event.transcript
            )
