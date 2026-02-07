import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from tasks.idle import IdleWatchdog
from utils.systemctl import Systemctl
from utils.minecraft import MinecraftServer

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
BACKEND = os.getenv("BACKEND", "local")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
systemctl = Systemctl(BACKEND)
minecraft = MinecraftServer(systemctl)
idle_watchdog = IdleWatchdog(minecraft)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    bot.loop.create_task(idle_watchdog.run(bot))
    await bot.tree.sync(guild=guild)
    print("Commands synced")


@bot.tree.command(name="mc_status", description="Check Minecraft server status")
async def mc_status(interaction: discord.Interaction):
    status = minecraft.status()
    await interaction.response.send_message(f"Minecraft is **{status}**")


@bot.tree.command(name="mc_start", description="Start the Minecraft server")
async def mc_start(interaction: discord.Interaction):
    result = minecraft.start()
    await interaction.response.send_message(f"Minecraft: {result}")


@bot.tree.command(name="mc_stop", description="Stop the Minecraft server")
async def mc_stop(interaction: discord.Interaction):
    result = minecraft.stop()
    await interaction.response.send_message(f"Minecraft: {result}")


bot.run(TOKEN)
