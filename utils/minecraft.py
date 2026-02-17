import os
import re
from dotenv import load_dotenv
from mcipc.rcon.je import Client
from utils.systemctl import Systemctl

load_dotenv()

RCON_HOST = "127.0.0.1"
RCON_PORT = 25575
RCON_PASSWORD = os.getenv("RCON_PASSWORD")
COLOR_CODE_RE = re.compile(r"§.")
PLAYER_COUNT_RE = re.compile(r"There are (\d+) out of maximum")

def get_player_count() -> int | None:
    if not RCON_PASSWORD:
        print("[WARN] RCON password not set")
        return None

    try:
        with Client(
            RCON_HOST,
            RCON_PORT,
            passwd=RCON_PASSWORD,
            timeout=3
        ) as client:
            response = client.run("list")

        response = "".join(response).strip()
        
        response = COLOR_CODE_RE.sub("", response)

        match = PLAYER_COUNT_RE.search(response)
        if match:
            return int(match.group(1))

        print("[WARN] Unexpected RCON response:", response)
        return None

    except Exception as e:
        print(f"[WARN] RCON player count failed: {repr(e)}")
        return None


class MinecraftServer:
    def __init__(self, systemctl: Systemctl):
        self.systemctl = systemctl
        self.service_name = "minecraft"

    def status(self) -> str:
        return self.systemctl.is_active(self.service_name)

    def start(self):
        status = self.status()
        if status in ("active", "activating"):
            return "already starting"
        return self.systemctl.start(self.service_name)


    def stop(self) -> str:
        status = self.status()
        if status != "active":
            return "already stopped"
        return self.systemctl.stop(self.service_name)
