import inspect
import json
from typing import Callable, Literal, get_origin, get_args


def make_audio(audio: str):
    return {"type": "input_audio_buffer.append", "audio": audio}


def make_audio_commit():
    return {"type": "input_audio_buffer.commit"}


def tool_to_tool_json(tool: Callable):
    description = tool.__doc__
    name = tool.__name__
    properties = {}
    required = []
    for p in inspect.signature(tool).parameters.values():
        if p.annotation is str:
            property = {"type": "string"}
        elif p.annotation is int:
            property = {"type": "integer"}
        elif p.annotation is float:
            property = {"type": "number"}
        elif get_origin(p.annotation) is Literal:
            property = {
                "type": "string",
                "enum": list(get_args(p.annotation)),
            }
        else:
            raise NotImplementedError(f"annotation: {p.annotation}")
        properties[p.name] = property
        # TODO: Support optional args
        required.append(p.name)

    parameters = {
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


def make_response_create(tools: list[Callable]):
    session_tools = []
    for tool in tools:
        tool = tool_to_tool_json(tool)
        session_tools.append(tool)
    return {
        "type": "response.create",
        "response": {
            "tools": session_tools,
        },
    }


def make_session_update(tools: list[Callable]):
    session_tools = []
    for tool in tools:
        tool = tool_to_tool_json(tool)
        session_tools.append(tool)
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
