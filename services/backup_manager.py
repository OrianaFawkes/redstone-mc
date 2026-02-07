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
