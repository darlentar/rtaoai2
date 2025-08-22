import inspect
import json
from typing import Any, Callable, Literal, get_args, get_origin, get_args, get_origin


def make_audio(audio: str):
    return {"type": "input_audio_buffer.append", "audio": audio}


def make_audio_commit():
    return {"type": "input_audio_buffer.commit"}


def tool_to_tool_json(tool: Callable) -> dict[str, Any]:
    description = tool.__doc__
    name = tool.__name__
    properties: dict[str, dict[str, Any]] = {}
    required: list[str] = []
    for p in inspect.signature(tool).parameters.values():
        if p.annotation is str:
            prop: dict[str, Any] = {"type": "string"}
        elif p.annotation is int:
            prop = {"type": "integer"}
        elif p.annotation is float:
            prop = {"type": "number"}
        elif get_origin(p.annotation) is Literal:
            prop = {
                "type": "string",
                "enum": list(get_args(p.annotation)),
            }
        else:
            raise NotImplementedError(f"annotation: {p.annotation}")
        properties[p.name] = prop
        # TODO: Support optional args
        required.append(p.name)

    parameters: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "required": required,
    }
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": parameters,
    }


def make_response_create(tools: list[Callable]) -> dict[str, Any]:
    session_tools: list[dict[str, Any]] = []
    for tool_fn in tools:
        session_tools.append(tool_to_tool_json(tool_fn))
    return {
        "type": "response.create",
        "response": {
            "tools": session_tools,
        },
    }


def make_session_update(tools: list[Callable]) -> dict[str, Any]:
    session_tools: list[dict[str, Any]] = []
    for tool_fn in tools:
        session_tools.append(tool_to_tool_json(tool_fn))
    return {
        "type": "session.update",
        "session": {
            "tools": session_tools,
            "input_audio_transcription": {"model": "whisper-1"},
            #      "turn_detection":None,
            #      "voice":"alloy",
        },
    }


class OpenAIEventProducer:
    def __init__(self, websocket):
        self.websocket = websocket

    async def make_audio(self, audio: str):
        await self.websocket.send(json.dumps(make_audio(audio)))

    async def make_audio_commit(self):
        await self.websocket.send(json.dumps(make_audio_commit()))

    async def make_response_create(self, tools: list[Callable]):
        await self.websocket.send(json.dumps(make_response_create(tools)))

    async def make_session_update(self, tools: list[Callable]):
        await self.websocket.send(json.dumps(make_session_update(tools)))
