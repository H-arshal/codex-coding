import asyncio

import pyautogui
import screeninfo
import websockets

# Get primary screen dimensions
screen = screeninfo.get_monitors()[0]
SCREEN_WIDTH = screen.width
SCREEN_HEIGHT = screen.height

EDGE_THRESHOLD = 5  # Pixels from right edge to trigger transfer mode
EXIT_THRESHOLD = 50  # Pixels from right edge to exit transfer mode
TICK_SECONDS = 0.03

connected_clients: set[websockets.WebSocketServerProtocol] = set()


async def handler(websocket: websockets.WebSocketServerProtocol) -> None:
    connected_clients.add(websocket)
    print("✅ Android connected!")
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.discard(websocket)
        print("❌ Android disconnected")


async def broadcast_cursor(rel_x: float, rel_y: float) -> None:
    if not connected_clients:
        return

    message = f"{rel_x:.6f},{rel_y:.6f}"
    await asyncio.gather(
        *[client.send(message) for client in connected_clients],
        return_exceptions=True,
    )


async def track_cursor() -> None:
    in_phone_mode = False

    while True:
        x, y = pyautogui.position()

        if x >= SCREEN_WIDTH - EDGE_THRESHOLD:
            in_phone_mode = True

        if in_phone_mode:
            # Clamp cursor to right edge on laptop.
            pyautogui.moveTo(SCREEN_WIDTH - 2, y)

            # Cursor is always on left edge of phone while y maps proportionally.
            rel_x = 0.0
            rel_y = max(0.0, min(1.0, y / SCREEN_HEIGHT))
            await broadcast_cursor(rel_x, rel_y)

        if x < SCREEN_WIDTH - EXIT_THRESHOLD:
            in_phone_mode = False

        await asyncio.sleep(TICK_SECONDS)


async def main() -> None:
    print(f"🖥️ Screen: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    print("🚀 Starting cursor server on ws://0.0.0.0:8765")
    print("📱 Open cursor_receiver.html on your Android device now!")

    async with websockets.serve(handler, "0.0.0.0", 8765):
        await track_cursor()


if __name__ == "__main__":
    asyncio.run(main())
