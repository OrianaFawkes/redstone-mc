import os
import re
from pathlib import Path
from utils.systemctl import Systemctl

BACKEND = os.getenv("BACKEND", "local")
LOG_FILE = Path("/home/orianafawkes/minecraft-server/logs/latest.log")
PLAYER_COUNT_RE = re.compile(r"There are (\d+) of a max")


def get_player_count() -> int:
    if not LOG_FILE.exists():
        return 0

    try:
        with LOG_FILE.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-100:]  # only scan recent lines

        for line in reversed(lines):
            match = PLAYER_COUNT_RE.search(line)
            if match:
                return int(match.group(1))

    except Exception as e:
        print(f"[WARN] Failed to read player count: {e}")

    return 0


class MinecraftServer:
    def __init__(self, systemctl: Systemctl):
        self.systemctl = systemctl
        self.service_name = "minecraft"

    def status(self) -> str:
        return self.systemctl.is_active(self.service_name)

    def start(self) -> str:
        status = self.status()
        if status == "active":
            return "already running"
        return self.systemctl.start(self.service_name)

    def stop(self) -> str:
        status = self.status()
        if status != "active":
            return "already stopped"
        return self.systemctl.stop(self.service_name)
