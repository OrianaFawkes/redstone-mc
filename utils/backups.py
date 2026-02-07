import os
import subprocess

BACKEND = os.getenv("BACKEND", "local")


class BackupExecutor:
    def run(self) -> bool:
        if BACKEND == "local":
            print("[LOCAL] Would run backup-mc.sh")
            return True

        result = subprocess.run(
            ["/home/orianafawkes/backup-mc.sh"], capture_output=True
        )
        return result.returncode == 0
