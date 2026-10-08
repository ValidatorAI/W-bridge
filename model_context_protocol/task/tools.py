from typing import Any, Callable


def hello(name: str = "World", **kwargs: Any) -> str:
    return f"Hello, {name}!"


TOOL_HANDLERS: dict[str, Callable[..., Any]] = {
    "hello": hello,
}


TOOL_DEFINITIONS = [
    {
        "name": "hello",
        "description": "Say hello to a given name or the world",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name to greet",
                    "default": "World",
                }
            },
        },
    }
]


__all__ = ["TOOL_DEFINITIONS", "TOOL_HANDLERS", "hello"]
