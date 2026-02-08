import asyncio
import os
import discord
import time
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from tasks.idle import IdleWatchdog
from utils.systemctl import Systemctl
from utils.minecraft import MinecraftServer

load_dotenv()

IDLE_TIMEOUT = 10 * 60

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID", 0)
BACKUP_CHANNEL_ID = os.getenv("BACKUP_CHANNEL_ID", 0)
BACKEND = os.getenv("BACKEND", "local")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
systemctl = Systemctl(BACKEND)
minecraft = MinecraftServer(systemctl)
idle_watchdog = IdleWatchdog(minecraft, BACKUP_CHANNEL_ID)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    idle_watchdog.last_nonempty = time.time()
    idle_watchdog.stopped_due_to_idle = False
    idle_watchdog.persist()

    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    bot.loop.create_task(idle_watchdog.run(bot))

    await bot.tree.sync(guild=guild)

    print("Commands synced")


@bot.tree.command(name="mc_status", description="Check Minecraft server status")
async def mc_status(interaction: discord.Interaction):
    status = await asyncio.to_thread(minecraft.status)

    await interaction.response.send_message(f"Minecraft is **{status}**")


@bot.tree.command(name="mc_start", description="Start the Minecraft server")
async def mc_start(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    result = await asyncio.to_thread(minecraft.start)

    await interaction.followup.send(f"Minecraft: {result}")


@bot.tree.command(name="mc_stop")
async def mc_stop(interaction: discord.Interaction):
    if interaction.guild is None or interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(
            "Only the server owner can use this command.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(thinking=True)

    result = await asyncio.to_thread(minecraft.stop)

    idle_watchdog.notify_server_started()

    await interaction.followup.send(f"Minecraft: {result}")


@bot.tree.command(name="mc_restart", description="Restart the Minecraft server")
async def mc_restart(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    status = await asyncio.to_thread(minecraft.status)

    if status == "active":
        await asyncio.to_thread(minecraft.stop)

    result = await asyncio.to_thread(minecraft.start)

    idle_watchdog.notify_server_started()

    await interaction.followup.send("Minecraft server restarted.")


@bot.tree.command(name="mc_idle", description="Show idle shutdown status")
async def mc_idle(interaction: discord.Interaction):
    status = await asyncio.to_thread(minecraft.status)

    if status != "active":
        await interaction.response.send_message(
            "Minecraft server is currently **offline**."
        )
        return

    idle_for = int(time.time() - idle_watchdog.last_nonempty)
    remaining = max(0, IDLE_TIMEOUT - idle_for)

    mins_idle = idle_for // 60
    mins_left = remaining // 60
    secs_left = remaining % 60

    await interaction.response.send_message(
        f"**Minecraft is online**\n"
        f"Idle for: **{mins_idle} min**\n"
        f"Auto shutdown in: **{mins_left} min {secs_left} sec**"
    )


@bot.tree.command(name="mc_backup", description="Run a manual Minecraft backup")
async def mc_backup(interaction: discord.Interaction):
    if interaction.guild is None or interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(
            "Only the server owner can use this command.",
            ephemeral=True,
        )
        return
    
    await interaction.response.defer(thinking=True)

    success, info = await asyncio.to_thread(
        idle_watchdog.backups.run_with_info, "manual"
    )

    if success:
        await interaction.followup.send(
            f"Backup completed successfully\n"
            f"File: `{info['file']}`\n"
            f"Size: {info['size_mb']} MB"
        )
    else:
        await interaction.followup.send(
            f"Backup failed\n"
            f"Error: `{info}`"
        )


@bot.tree.command(name="mc_backup_status", description="Show backup status and limits")
async def mc_backup_status(interaction: discord.Interaction):
    state = idle_watchdog.backups.state

    await interaction.response.send_message(
        f"**Backup status**\n"
        f"Today: {state.daily}\n"
        f"This week: {state.weekly}"
    )


bot.run(TOKEN)
