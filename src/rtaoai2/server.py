import io
import asyncio
import json
import os
import base64

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import websockets

from rtaoai2.openai.consumer import OpenAIEventConsumer, OpenAIStreamingEventConsummer
from rtaoai2.openai.producer import OpenAIEventProducer
from rtaoai2.ui.consumer import EventConsumer
from rtaoai2.ui.producer import EventProducer

from pydub import AudioSegment


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
async def websocket_endpoint(websocket: WebSocket):
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

    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
    headers = {
        "Authorization": f"Bearer {os.environ["OPENAI_API_KEY"]}",
        "OpenAI-Beta": "realtime=v1",
    }
    openai_ws = await websockets.connect(url, extra_headers=headers)

    openai_event_producer = OpenAIEventProducer(openai_ws)
    await openai_event_producer.make_session_update(tools=[])
    ui_event_consumer = EventConsumer(openai_event_producer)

    ui_event_producer = EventProducer(websocket)
    openai_event_consumer = OpenAIStreamingEventConsummer(
        OpenAIEventConsumer(), ui_event_producer
    )

    async def client_websocket_handler():
        while True:
            data = await websocket.receive()

            if "bytes" in data:
                await ui_event_consumer.on_audio(
                    audio_to_item_create_event(data["bytes"])
                )
                await ui_event_consumer.on_response_create(tools=[])

    async def openai_websocket_handler():
        async for e in openai_ws:
            await openai_event_consumer.on_event(json.loads(e))

    await websocket.accept()

    await asyncio.gather(openai_websocket_handler(), client_websocket_handler())
