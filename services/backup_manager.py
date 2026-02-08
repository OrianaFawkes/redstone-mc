import os
from utils.backup_state import BackupState
from utils.backups import BackupExecutor


class BackupManager:
    def __init__(self):
        self.state = BackupState()
        self.executor = BackupExecutor()

    def maybe_backup(self, reason: str):
        if not self.state.can_backup():
            print(f"Backup skipped (limit reached) [{reason}]")
            return False

        print(f"Running backup ({reason})")
        success = self.executor.run()

        if success:
            self.state.record_backup()
            print("Backup complete")
        else:
            print("Backup failed")

        return success

    def run_with_info(self, reason: str):
        if not self.state.can_backup():
            return False, "Backup limit reached"

        success, output = self.executor.run()

        if success:
            self.state.record_backup()

            # Parse destination path from script output
            # "Backup completed: /path/to/file.tar.gz"
            dest = output.split(": ", 1)[-1]
            size_mb = round(os.path.getsize(dest) / (1024 * 1024), 1)

            return True, {
                "file": os.path.basename(dest),
                "size_mb": size_mb,
            }

        return False, output