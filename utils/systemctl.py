import os
import subprocess

from dotenv import load_dotenv

load_dotenv()

BACKEND = os.getenv("BACKEND", "local")


class Systemctl:
    def __init__(self, backend: str | None = None):
        self.backend = backend or BACKEND

    def is_active(self, service: str) -> str:
        if self.backend == "local":
            return "inactive (local dev)"

        result = subprocess.run(
            ["systemctl", "is-active", service], capture_output=True, text=True
        )
        return result.stdout.strip()

    def start(self, service: str) -> str:
        if self.backend == "local":
            return f"started {service} (local dev)"

        subprocess.run(["sudo", "systemctl", "start", service], check=False)
        return "started"

    def stop(self, service: str) -> str:
        if self.backend == "local":
            return f"stopped {service} (local dev)"

        subprocess.run(["sudo", "systemctl", "stop", service], check=False)
        return "stopped"
