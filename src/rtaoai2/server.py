import io
import asyncio
import os
import base64

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import Message as WebSocketMessage
from pydub import AudioSegment  # type: ignore[import-untyped]
from openai import AsyncOpenAI

from rtaoai2.ui.consumer import EventConsumer
from rtaoai2.ui.producer import EventProducer


def audio_to_item_create_event(audio_bytes: bytes) -> str:
    # Load the audio file from the byte stream
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))

    # Resample to 24kHz mono pcm16
    pcm_audio = audio.set_frame_rate(24000).set_channels(1).set_sample_width(2).raw_data

    # Encode to base64 string
    return base64.b64encode(pcm_audio).decode()


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    def get_product_remaining_stock(product_id: int) -> int:
        """Get product remaining stock given a product id."""
        try:
            return [1, 23, 244, 344, 123][product_id]
        except IndexError:
            return 0

    def list_all_products() -> list[int]:
        """List all available products. Returns a list of int."""
        return list(range(20))

    # async def on_output_item_done(output_item: OutputItemDone):
    #     # TODO: make it dynamic
    #     if output_item.item.name == "get_product_remaining_stock":
    #         if output_item.item.arguments is None:
    #             raise ValueError("arguments can't be None")
    #         params = json.loads(output_item.item.arguments)
    #         result = get_product_remaining_stock(**params)
    #         send_json = json.dumps(
    #             {
    #                 "type": "conversation.item.create",
    #                 "item": {
    #                     "call_id": output_item.item.call_id,
    #                     "type": "function_call_output",
    #                     # "role": "system",
    #                     "output": str(result),
    #                 },
    #             }
    #         )
    #         await openai_runner.ws.send(send_json)
    #         await openai_runner.ws.send(json.dumps({"type": "response.create"}))
    #     elif output_item.item.name == "list_all_products":
    #         list_products_result = list_all_products()
    #         send_json = json.dumps(
    #             {
    #                 "type": "conversation.item.create",
    #                 "item": {
    #                     "call_id": output_item.item.call_id,
    #                     "type": "function_call_output",
    #                     # "role": "system",
    #                     "output": str(list_products_result),
    #                 },
    #             }
    #         )

    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    async with client.realtime.connect(
        model="gpt-4o-realtime-preview-2024-10-01",
        headers={"OpenAI-Beta": "realtime=v1"},
    ) as openai_ws:
        await openai_ws.session.update(
            session={
                "tools": [],
                "input_audio_transcription": {"model": "whisper-1"},
            }
        )
        ui_event_consumer = EventConsumer(openai_ws)
        ui_event_producer = EventProducer(websocket)

        async def client_websocket_handler() -> None:
            while True:
                data: WebSocketMessage = await websocket.receive()

                if "bytes" in data:
                    await ui_event_consumer.on_audio(
                        audio_to_item_create_event(data["bytes"])
                    )
                    await ui_event_consumer.on_response_create(tools=[])

        async def openai_websocket_handler() -> None:
            async for event in openai_ws:
                event_type = event.get("type")
                if event_type == "response.audio.delta":
                    await ui_event_producer.on_response_audio_delta_event(event.get("delta", ""))
                elif event_type == "response.audio_transcript.delta":
                    delta = event.get("delta")
                    if delta:
                        await ui_event_producer.on_response_audio_transcript_delta_event(delta)
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    await ui_event_producer.on_response_audio_input_transcript_done_event(
                        event.get("transcript", "")
                    )
                elif event_type == "response.done":
                    await ui_event_producer.on_response_done()

        await websocket.accept()

        await asyncio.gather(openai_websocket_handler(), client_websocket_handler())
