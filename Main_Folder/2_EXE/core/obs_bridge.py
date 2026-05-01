"""
core/obs_bridge.py
Writes live captions to caption_output.txt (OBS Text source reads this file).
Connects to OBS WebSocket v5 (OBS 28+) using raw websocket-client.
No obsws-python needed — just: pip install websocket-client
"""

import os
import json
import hashlib
import base64
import threading
from typing import Optional


class OBSBridge:
    def __init__(self, base_path: str):
        self.base_path    = base_path
        self.caption_file = os.path.join(base_path, "dist", "caption_output.txt")
        self._ws          = None
        self.connected    = False
        os.makedirs(os.path.dirname(self.caption_file), exist_ok=True)
        self.clear()

    # ── CAPTION FILE (always works, no OBS needed) ───────────────
    def update_caption(self, text: str):
        try:
            with open(self.caption_file, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"[OBS] Caption write error: {e}")

    def clear(self):
        self.update_caption("")

    # ── WEBSOCKET v5 (raw, no library issues) ────────────────────
    def connect_websocket(self, host: str = "localhost",
                          port: int = 4455,
                          password: str = "dsAWdU83PDTYCE1N") -> bool:
        try:
            import websocket

            ws_url = f"ws://{host}:{port}"
            print(f"[OBS] Connecting to {ws_url} ...")

            ws = websocket.WebSocket()
            ws.connect(ws_url, timeout=5)

            # Step 1: receive Hello message
            hello_raw = ws.recv()
            hello = json.loads(hello_raw)
            print(f"[OBS] Hello received: OBS WebSocket v{hello['d'].get('rpcVersion','?')}")

            # Step 2: build auth if required
            auth_data = hello["d"].get("authentication")
            identify_payload = {
                "op": 1,
                "d": {"rpcVersion": 1}
            }
            if auth_data and password:
                secret      = base64.b64encode(
                    hashlib.sha256((password + auth_data["salt"]).encode()).digest()
                ).decode()
                auth_string = base64.b64encode(
                    hashlib.sha256((secret + auth_data["challenge"]).encode()).digest()
                ).decode()
                identify_payload["d"]["authentication"] = auth_string

            # Step 3: send Identify
            ws.send(json.dumps(identify_payload))

            # Step 4: receive Identified
            identified_raw = ws.recv()
            identified     = json.loads(identified_raw)
            if identified.get("op") != 2:
                print(f"[OBS] Auth failed: {identified}")
                ws.close()
                return False

            self._ws       = ws
            self.connected = True
            print("[OBS] Connected ✅  WebSocket v5 authenticated successfully")
            return True

        except ConnectionRefusedError:
            print("[OBS] ⚠  Connection refused — is OBS open with WebSocket enabled?")
            return False
        except ImportError:
            print("[OBS] websocket-client not installed — run: pip install websocket-client")
            return False
        except Exception as e:
            print(f"[OBS] Connection failed: {e}")
            return False

    def disconnect(self):
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
        self._ws       = None
        self.connected = False

    @property
    def caption_path(self) -> str:
        return self.caption_file