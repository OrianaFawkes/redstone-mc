import asyncio
import time
from services.backup_manager import BackupManager
from utils.minecraft import get_player_count, MinecraftServer
from utils.state import load_state, save_state

IDLE_TIMEOUT = 10 * 60
CHECK_INTERVAL = 15


class IdleWatchdog:
    def __init__(self, mc: MinecraftServer, backup_channel_id: str):
        state = load_state()
        self.mc = mc
        self.backup_channel_id = backup_channel_id

        self.last_nonempty = state.get("last_nonempty", time.time())
        self.stopped_due_to_idle = state.get("stopped_due_to_idle", False)

        self.backups = BackupManager()

    async def notify_backup(self, bot, message: str):
        if not self.backup_channel_id:
            return

        channel = bot.get_channel(self.backup_channel_id)
        if channel:
            await channel.send(message)

    def notify_server_started(self):
        self.last_nonempty = time.time()
        self.stopped_due_to_idle = False
        self.persist()

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
            status = await asyncio.to_thread(self.mc.status)

            if status != "active":
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            try:
                players = get_player_count()
            except Exception as e:
                print(f"Player count failed: {e}")
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            if players > 0:
                self.last_nonempty = time.time()
                self.stopped_due_to_idle = False
                
            else:
                idle_time = time.time() - self.last_nonempty
                if idle_time >= IDLE_TIMEOUT and not self.stopped_due_to_idle:
                    print("Idle timeout reached ! stopping server")
                    
                    await asyncio.to_thread(self.mc.stop)

                    success, info = self.backups.run_with_info(reason="idle_stop")
                    if success:
                        await self.notify_backup(
                            bot,
                            f"Idle backup completed\n"
                            f"File: `{info['file']}` ({info['size_mb']} MB)"
                        )
                    else:
                        await self.notify_backup(
                            bot,
                            f"Idle backup FAILED\nReason: `{info}`"
                        )
                    
                    self.stopped_due_to_idle = True
                  
            self.persist()
            await asyncio.sleep(CHECK_INTERVAL)
