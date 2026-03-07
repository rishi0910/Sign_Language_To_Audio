"""
core/websocket_server.py
Broadcasts live translation data to the website frontend via WebSocket.
Port 8765 by default.
"""

import json
import threading
import asyncio
from datetime import datetime
from typing import Optional


class WebSocketServer:
    def __init__(self, port: int = 8765):
        self.port     = port
        self._clients = set()
        self._loop:   Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print(f"[WebSocket] Server starting on ws://localhost:{self.port}")

    def stop(self):
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def broadcast(self, word: str, sentence: str):
        if not self._clients or not self._loop:
            return
        payload = json.dumps({
            "word":      word,
            "sentence":  sentence,
            "timestamp": datetime.now().isoformat(),
        })
        asyncio.run_coroutine_threadsafe(self._send_all(payload), self._loop)

    # ── PRIVATE ─────────────────────────────────────────────────
    def _run_loop(self):
        try:
            import websockets
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            async def handler(ws, path):
                self._clients.add(ws)
                try:
                    await ws.wait_closed()
                finally:
                    self._clients.discard(ws)

            async def serve():
                async with websockets.serve(handler, "localhost", self.port):
                    await asyncio.Future()   # run forever

            self._loop.run_until_complete(serve())
        except ImportError:
            print("[WebSocket] 'websockets' package not installed — server disabled")
        except Exception as e:
            print(f"[WebSocket] Error: {e}")

    async def _send_all(self, message: str):
        dead = set()
        for client in self._clients:
            try:
                await client.send(message)
            except Exception:
                dead.add(client)
        self._clients -= dead
