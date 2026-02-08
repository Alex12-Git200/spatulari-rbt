import discord
from discord.ext import commands
import os
import yt_dlp
from discord.ext import tasks
import feedparser
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
LAST_TIKTOK_ID = None
LAST_VIDEO_ID = None
STATUS_MESSAGE_ID = None
YOUTUBE_CHANNEL_ID = "UCFVnjoLRjhiBJxkYNXUePjQ"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
user_cooldowns = {}

async def get_status_message():
    global STATUS_MESSAGE_ID

    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if not channel:
        return None

    # If we already know the message
    if STATUS_MESSAGE_ID:
        try:
            return await channel.fetch_message(STATUS_MESSAGE_ID)
        except discord.NotFound:
            STATUS_MESSAGE_ID = None

    # Look for an existing pinned status message
    async for msg in channel.pins():
        if msg.author == bot.user:
            STATUS_MESSAGE_ID = msg.id
            return msg

    # Create it if it doesn't exist
    embed = discord.Embed(
        title="🤖 Bot Status",
        description="🟡 Starting up...",
        color=0xffff00
    )

    msg = await channel.send(embed=embed)
    await msg.pin()
    STATUS_MESSAGE_ID = msg.id
    return msg


async def update_status(state: str):
    msg = await get_status_message()
    if not msg:
        return

    colors = {
        "online": 0x00ff00,
        "restarting": 0xffff00,
        "offline": 0xff0000
    }

    texts = {
        "online": "🟢 **Online** — Bot is running normally.",
        "restarting": "🟡 **Restarting** — Bot will be back shortly.",
        "offline": "🔴 **Offline** — Bot is shut down."
    }

    embed = discord.Embed(
        title="🤖 Bot Status",
        description=texts[state],
        color=colors[state]
    )

    await msg.edit(embed=embed)


def get_latest_video():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return None

    entry = feed.entries[0]
    return {
        "title": entry.title,
        "url": entry.link,
        "published": entry.published
    }

def get_youtube_audio(query):
    ydl_opts = {
        "quiet": True,
        "format": "bestaudio",
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        entry = info["entries"][0]
        return entry["id"], entry["title"]


# def get_latest_tiktok():
#     feed = feedparser.parse(TIKTOK_RSS_URL)
#     if not feed.entries:
#         return None

#     entry = feed.entries[0]
#     return {
#         "title": entry.title,
#         "url": entry.link,
#         "published": entry.published
#     }

def load_levels():
    try:
        with open(LEVELS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_levels(data):
    with open(LEVELS_FILE, "w") as f:
        json.dump(data, f, indent=4)


async def notify_owner(text):
    owner = await bot.fetch_user(MY_USER_ID)
    if owner:
        try:
            await owner.send(f"⚠️ **Bot Alert:** {text}")
        except:
            print(f"Failed to DM owner: {text}")



async def handle_member_join(member):
    print("🔥 handle_member_join CALLED")
    print("Member:", member)
    print("Guild:", member.guild)

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    print("Channel:", channel)
    print("Member top role:", member.top_role, member.top_role.position)
    print("Bot top role:", member.guild.me.top_role, member.guild.me.top_role.position)

    if channel:
        try:
            await channel.send(f"👋 Welcome {member.mention}! Enjoy your stay 😎")
            print("Welcome message sent")
        except discord.Forbidden:
            print("❌ No permission to send messages in welcome channel")

    try:
        await member.send("Welcome! Thanks for joining, don't break the rules")
        print("DM sent")
    except discord.Forbidden:
        print("DM blocked")

    role = member.guild.get_role(MEMBER_ROLE_ID)  
    print("Role:", role)

    if role and role not in member.roles:
        await member.add_roles(role)
        print("Role added")



@bot.event
async def on_ready():
    await update_status("online")

    if not check_youtube.is_running():
        check_youtube.start()


    print("Bot is online")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    user_id = str(message.author.id)
    current_time = time.time()
    
    if user_id not in user_cooldowns or current_time - user_cooldowns[user_id] > 60:
        levels = load_levels()
        
        if user_id not in levels:
            levels[user_id] = {"xp": 0, "level": 1}
        
        xp_gain = random.randint(15, 25)
        levels[user_id]["xp"] += xp_gain
        
        xp_needed = levels[user_id]["level"] * 100
        if levels[user_id]["xp"] >= xp_needed:
            levels[user_id]["level"] += 1
            levels[user_id]["xp"] = 0 
            
            new_level = levels[user_id]["level"]
            await message.channel.send(f"🎉 {message.author.mention} just hit **Level {new_level}**!")

            if new_level == 15:
                role = message.guild.get_role(TRUSTED_MEMBER_ROLE_ID)
                if role and role not in message.author.roles:
                    try:
                        await message.author.add_roles(role)
                        await message.channel.send(f"🛡️ **Level 15 achieved!** {message.author.mention} has been promoted to **Trusted Member**.")
                    except discord.Forbidden:
                        notify_owner(f"failed to add role to {message.author.name}")
                        print("❌ Failed to add role: Check bot permissions/hierarchy.")

        save_levels(levels)
        user_cooldowns[user_id] = current_time


    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    await handle_member_join(member)



@tasks.loop(minutes=5)
async def check_youtube():
    global LAST_VIDEO_ID

    video = get_latest_video()
    if video is None:
        return

    video_id = video["url"]

    if video_id == LAST_VIDEO_ID:
        return

    LAST_VIDEO_ID = video_id

    channel = bot.get_channel(YT_ANNOUNCE_CHANNEL_ID)
    if channel:
        await channel.send(
            f"📢 @everyone **New YouTube video!**\n"
            f"🎬 **{video['title']}**\n"
            f"🔗 {video['url']}"
        )

@check_youtube.before_loop
async def before_check_youtube():
    global LAST_VIDEO_ID
    await bot.wait_until_ready()

    video = get_latest_video()
    if video:
        LAST_VIDEO_ID = video["url"]
        print("📌 Initial YouTube video set:", video["title"])


@bot.command()
@commands.has_role(OWNER_ROLE_ID)
async def testjoin(ctx):
    await handle_member_join(ctx.author)

@testjoin.error
async def testjoin_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ You don't have permission to use this.")

@bot.command()
@commands.has_role(OWNER_ROLE_ID)
async def testytpost(ctx):
    video = get_latest_video()
    if video is None:
        await ctx.send("❌ No videos found on the channel.")
        return

    channel = bot.get_channel(YT_ANNOUNCE_CHANNEL_ID)
    if channel is None:
        await ctx.send("❌ Announce channel not found.")
        return

    await channel.send(
        f"🧪 **TEST: New YouTube video!**\n"
        f"🎬 **{video['title']}**\n"
        f"🔗 {video['url']}"
    )

    await ctx.send("✅ Test YouTube post sent.")

@testytpost.error
async def testytpost_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ You don't have permission to use this.")



@bot.command()
@commands.has_role(OWNER_ROLE_ID)
async def exit(ctx):
    await update_status("offline")
    await ctx.send("Bye 👋")
    await bot.close()
    sys.exit(0)

@bot.command()
@commands.check(command_channel)
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    levels = load_levels()
    user_id = str(member.id)
    
    if user_id not in levels:
        await ctx.send("No rank data yet. Start chatting!")
        return
        
    xp = levels[user_id]['xp']
    lvl = levels[user_id]['level']
    needed = lvl * 100
    
    await ctx.send(f"📊 **{member.name}** | Level: **{lvl}** | XP: **{xp}/{needed}**")

@bot.command()
@commands.check(command_channel)
async def leaderboard(ctx):
    levels = load_levels()
    # Sort by Level, then XP
    sorted_users = sorted(levels.items(), key=lambda x: (x[1]['level'], x[1]['xp']), reverse=True)
    
    msg = "🏆 **Top Chatters**\n"
    for i, (u_id, data) in enumerate(sorted_users[:5], 1):
        user = bot.get_user(int(u_id))
        name = user.name if user else "Unknown"
        msg += f"{i}. **{name}** - Level {data['level']}\n"

    await ctx.send(msg)

@bot.command()
@commands.has_role(OWNER_ROLE_ID)
async def restart(ctx):
    await ctx.send("♻️ Restarting bot...")


    await update_status("restarting")

    await asyncio.sleep(10)

    # Restart the process FIRST
    os.execv(sys.executable, [sys.executable] + sys.argv)


async def load_cogs():
    await bot.load_extension("cogs.core")
    await bot.load_extension("cogs.utils")
    await bot.load_extension("cogs.fun")
    await bot.load_extension("cogs.moderation")
    await bot.load_extension("cogs.music")


asyncio.run(load_cogs())
bot.run(TOKEN_STR)
