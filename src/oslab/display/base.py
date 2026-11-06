"""Frame source interface."""
from typing import Protocol


class FrameSource(Protocol):
    name: str

    async def attach(self, ws) -> None:
        """Bridge one websocket to one frame stream until either side closes."""
