import discord
from discord.ext import commands
import os
import yt_dlp
import random
import time
from datetime import timedelta
import json
import sys
import asyncio
from bot_token import TOKEN_STR
from config import *
from utils.checks import command_channel

START_TIME = time.time()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = commands.Bot(command_prefix="!", intents=intents)
bot.start_time = time.time()

bot.remove_command("help")


TIKTOK_USERNAME = "spatulari"
TIKTOK_RSS_URL = f"https://rsshub.app/tiktok/user/{TIKTOK_USERNAME}"
STATUS_MESSAGE_ID = None

async def notify_owner(text):
    owner = await bot.fetch_user(MY_USER_ID)
    if owner:
        try:
            await owner.send(f"⚠️ **Bot Alert:** {text}")
        except:
            print(f"Failed to DM owner: {text}")

@bot.event
async def setup_hook():
    await bot.load_extension("cogs.core")
    await bot.load_extension("cogs.utils")
    await bot.load_extension("cogs.fun")
    await bot.load_extension("cogs.moderation")
    await bot.load_extension("cogs.music")
    await bot.load_extension("cogs.xp")
    await bot.load_extension("cogs.welcome") 
    await bot.load_extension("cogs.ytcheck")
    await bot.load_extension("cogs.status")

@bot.event
async def on_ready():
    status = bot.get_cog("Status")
    if status:
        await status.update_status("online")

    print("Bot is online")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    


    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    pass


@bot.command()
@commands.has_role(OWNER_ROLE_ID)
async def exit(ctx):
    status = ctx.bot.get_cog("Status")
    if status:
        await status.update_status("offline")
    await ctx.send("Bye 👋")
    await bot.close()
    sys.exit(0)

@bot.command()
@commands.has_role(OWNER_ROLE_ID)
async def restart(ctx):
    await ctx.send("♻️ Restarting bot...")


    status = ctx.bot.get_cog("Status")
    if status:
        await status.update_status("restarting")

    await asyncio.sleep(10)

    # Restart the process FIRST
    os.execv(sys.executable, [sys.executable] + sys.argv)

bot.run(TOKEN_STR)
