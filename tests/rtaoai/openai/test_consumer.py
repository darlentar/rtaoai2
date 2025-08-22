from typing import Any

import pytest

from rtaoai2.openai.consumer import (
    OpenAIEventConsumer,
    UnknownEventError,
    OpenAIStreamingEventConsumer,
    OpenAIWaitInputTranscriptEventConsumer,
)
from rtaoai2.openai.events import ResponseAudioDeltaEvent


@pytest.fixture
def event():
    return {"type": "response.audio.delta", "delta": "12345"}


def test_process_response_audio_delta_event(event):
    event = OpenAIEventConsumer().process_event(event)
    assert isinstance(event, ResponseAudioDeltaEvent)


def test_process_unhandled_event():
    with pytest.raises(UnknownEventError):
        OpenAIEventConsumer().process_event({"type": "unknown_event"})


class TranscriptQueueSpy:
    def __init__(self) -> None:
        self.events: list[tuple[str, str | None]] = []

    async def on_response_audio_delta_event(self, event: Any) -> None:
        pass

    async def on_response_audio_transcript_delta_event(self, transcript: str) -> None:
        self.events.append(("transcript", transcript))

    async def on_response_audio_input_transcript_done_event(self, event: Any) -> None:
        pass

    async def on_response_created(self, event: Any) -> None:
        pass

    async def on_response_done(self, event: Any) -> None:
        self.events.append(("done", None))


@pytest.mark.asyncio
async def test_flush_transcript_queue_before_done() -> None:
    spy = TranscriptQueueSpy()
    consumer = OpenAIWaitInputTranscriptEventConsumer(
        event_consumer=OpenAIEventConsumer(), response_producer=spy
    )
    await consumer.on_event(
        {"type": "response.audio_transcript.delta", "delta": "Hello"}
    )
    await consumer.on_event(
        {"type": "response.audio_transcript.delta", "delta": " world"}
    )
    await consumer.on_event({"type": "response.done"})

    assert spy.events == [("transcript", "Hello world"), ("done", None)]
    assert consumer.response_audio_transcript_queue == ""


create_response = "crate_response"
play_audio = "play_audio"
write_input_transcript = "write_input_transcript"
write_transcript = "write_transcript"
end_response = "end_response"


class ResponseProducerSpy:
    def __init__(self):
        self.events = []

    async def on_response_audio_delta_event(self, event):
        self.events.append(play_audio)

    async def on_response_audio_transcript_delta_event(self, event):
        self.events.append(write_transcript)

    async def on_response_audio_input_transcript_done_event(self, event):
        self.events.append(write_input_transcript)

    async def on_response_created(self, event):
        self.events.append(create_response)

    async def on_response_done(self, event):
        self.events.append(end_response)


@pytest.mark.asyncio
async def test_producer_spy(events_json):
    response_producer_spy = ResponseProducerSpy()
    events_consumer = OpenAIWaitInputTranscriptEventConsumer(
        event_consumer=OpenAIEventConsumer(), response_producer=response_producer_spy
    )
    for e in events_json("."):
        await events_consumer.on_event(e)
    assert response_producer_spy.events == [
        create_response,
        play_audio,
        play_audio,
        play_audio,
        play_audio,
        write_transcript,
        end_response,
        write_input_transcript,
        create_response,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        end_response,
        create_response,
        play_audio,
        play_audio,
        play_audio,
        play_audio,
        play_audio,
        play_audio,
        play_audio,
        play_audio,
        write_input_transcript,
        write_transcript,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        write_transcript,
        play_audio,
        end_response,
    ]


class ResponseProducerConsoleSpy:
    def __init__(self):
        self.events = []

    async def on_response_audio_delta_event(self, event):
        self.events.append(("write_response_audio", ""))

    async def on_response_audio_transcript_delta_event(self, transcript):
        self.events.append(("write_response_transcript", transcript))

    async def on_response_audio_input_transcript_done_event(self, transcript):
        self.events.append(("write_input_transcript", transcript))

    async def on_response_created(self, event):
        pass

    async def on_response_done(self, event):
        pass


@pytest.fixture
def transcript_before_input_audio_transcript_event():
    return [
        "Sure",
        " you",
        " have",
        " options",
        ".",
        " many",
        " countries",
        " due",
    ]


@pytest.fixture
def transcript_remaining():
    return [
        " to",
        " flight",
        " networks",
        " can",
        " easily",
        ".",
        "1",
        "itzerland",
        "\n",
        " Spain",
        "\n",
        " Netherlands",
        "\n",
        "ugal",
        "\n",
        " just",
        " a",
        " destination",
        " you're",
    ]


@pytest.mark.asyncio
async def test_response_producer_ui(
    transcript_before_input_audio_transcript_event,
    transcript_remaining,
    events_json,
):
    expected_events = []
    # first we received transcript with audio, in UI we don't have
    # to wait for input audio transcript ending
    for e in transcript_before_input_audio_transcript_event:
        expected_events.append(("write_response_transcript", e))
        expected_events.append(("write_response_audio", ""))

    # then we received the input transcript
    expected_events.append(
        (
            "write_input_transcript",
            "Oui, j'aimerais savoir s'il y a quelque chose que je peux faire et si vous pouvez me lister tous les pays que je peux acc\u00e9der \u00e0 de Paris.\n",
        )
    )

    # then remaining events
    for e in transcript_remaining:
        expected_events.append(("write_response_transcript", e))
        expected_events.append(("write_response_audio", ""))

    response_producer_spy = ResponseProducerConsoleSpy()
    events_consumer = OpenAIStreamingEventConsumer(
        event_consumer=OpenAIEventConsumer(), response_producer=response_producer_spy
    )
    for e in events_json(".")[48:]:
        await events_consumer.on_event(e)
    assert response_producer_spy.events == expected_events


@pytest.mark.asyncio
async def test_response_producer_console(
    transcript_before_input_audio_transcript_event,
    transcript_remaining,
    events_json,
):
    # first we have audio tuple without transcript as we do not have audio input transcript yet
    expected_events = [("write_response_audio", "")] * len(
        transcript_before_input_audio_transcript_event
    )

    # then we received the input audio transcript so we can write it
    expected_events.append(
        (
            "write_input_transcript",
            "Oui, j'aimerais savoir s'il y a quelque chose que je peux faire et si vous pouvez me lister tous les pays que je peux acc\u00e9der \u00e0 de Paris.\n",
        )
    )

    # we then write the already received audio transcript
    expected_events.append(
        (
            "write_response_transcript",
            "".join(
                [
                    transcript
                    for transcript in transcript_before_input_audio_transcript_event
                ]
            ),
        )
    )

    # then for each event we display the transcript and play the audio
    for e in transcript_remaining:
        expected_events.append(("write_response_transcript", e))
        expected_events.append(("write_response_audio", ""))

    response_producer_spy = ResponseProducerConsoleSpy()
    events_consumer = OpenAIWaitInputTranscriptEventConsumer(
        event_consumer=OpenAIEventConsumer(), response_producer=response_producer_spy
    )
    for e in events_json(".")[48:]:
        await events_consumer.on_event(e)
    assert response_producer_spy.events == expected_events
