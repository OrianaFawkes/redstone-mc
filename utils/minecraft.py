import os
import re
from mcrcon import MCRcon
from pathlib import Path
from utils.systemctl import Systemctl

BACKEND = os.getenv("BACKEND", "local")
LOG_FILE = Path("/home/orianafawkes/minecraft-server/logs/latest.log")

RCON_HOST = "127.0.0.1"
RCON_PORT = 25575
RCON_PASSWORD = "your_secure_password"

LIST_RE = re.compile(r"There are (\d+) of a max")

def get_player_count() -> int | None:
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command("list")

        match = LIST_RE.search(response)
        if match:
            return int(match.group(1))

        print("[WARN] Unexpected RCON list response:", response)
        return None

    except Exception as e:
        print(f"[WARN] RCON player count failed: {e}")
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
