import os
import subprocess

BACKEND = os.getenv("BACKEND", "local")


class BackupExecutor:
    def run(self) -> tuple[bool, str]:
        if BACKEND == "local":
            return True, "[LOCAL] backup skipped"

        result = subprocess.run(
            ["/home/orianafawkes/backup-mc.sh", "daily"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return False, result.stderr.strip()

        return True, result.stdout.strip()

