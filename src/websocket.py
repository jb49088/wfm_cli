import asyncio
import json

import websockets

from config import AUTH_MESSAGE, WS_URI


async def open_websocket(
    cookie_header: dict[str, str],
    state: dict[str, str],
    initial_status_event: asyncio.Event,
    status_queue: asyncio.Queue,
) -> None:
    """Connect to WebSocket, authenticate, and manage status updates."""
    async with websockets.connect(
        uri=WS_URI,
        additional_headers=cookie_header,
    ) as ws:
        await ws.send(AUTH_MESSAGE)

        current_response_event = None

        async def send_status_updates():
            """Send status updates from the queue to the WebSocket."""
            nonlocal current_response_event

            while True:
                status_message, response_event = await status_queue.get()
                await ws.send(status_message)
                current_response_event = response_event

        async def receive_messages():
            """Receive messages from the WebSocket."""
            nonlocal current_response_event

            while True:
                message = json.loads(await ws.recv())
                payload_status = message.get("payload", {}).get("status")

                if payload_status:
                    state["status"] = payload_status
                    initial_status_event.set()

                    if current_response_event:
                        current_response_event.set()
                        current_response_event = None

        await asyncio.gather(receive_messages(), send_status_updates())
