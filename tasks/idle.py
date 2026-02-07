import asyncio
import time
from services.backup_manager import BackupManager
from utils.minecraft import get_player_count, MinecraftServer
from utils.state import load_state, save_state

IDLE_TIMEOUT = 10 * 60
CHECK_INTERVAL = 15


class IdleWatchdog:
    def __init__(self, mc: MinecraftServer):
        state = load_state()
        self.mc = mc
        self.last_nonempty = state.get("last_nonempty", time.time())
        self.stopped_due_to_idle = state.get("stopped_due_to_idle", False)
        self.backups = BackupManager()

    def persist(self):
        save_state(
            {
                "last_nonempty": self.last_nonempty,
                "stopped_due_to_idle": self.stopped_due_to_idle,
            }
        )

    async def run(self, bot):
        await bot.wait_until_ready()
        print("Idle watchdog started")

        while not bot.is_closed():
            players = get_player_count()

            if players > 0:
                self.last_nonempty = time.time()
                self.stopped_due_to_idle = False
                self.persist()
            else:
                idle_time = time.time() - self.last_nonempty
                self.persist()
                if idle_time >= IDLE_TIMEOUT and not self.stopped_due_to_idle:
                    print("Idle timeout reached — stopping server")
                    self.mc.stop()
                    self.backups.maybe_backup(reason="idle_stop")
                    self.stopped_due_to_idle = True
                    self.persist()

            await asyncio.sleep(CHECK_INTERVAL)
