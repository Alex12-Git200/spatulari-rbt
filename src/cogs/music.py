import discord
from discord.ext import commands
import os
import yt_dlp
from utils.checks import command_channel
from config import *


def music_channel_commands(ctx):
    return ctx.channel.id == MUSIC_COMMANDS_CHANNEL_ID


def get_state(bot, guild_id):
    if not hasattr(bot, "music"):
        bot.music = {}

    if guild_id not in bot.music:
        bot.music[guild_id] = {
            "queue": [],
            "loop": False
        }

    return bot.music[guild_id]


def create_source(path):
    volume_filter = f"-filter:a volume={VOLUME / 100}"
    return discord.FFmpegOpusAudio(
        executable="ffmpeg.exe",
        source=path,
        options=f"-vn {volume_filter}",
        bitrate=128
    )


def play_next(ctx):
    state = get_state(ctx.bot, ctx.guild.id)
    vc = ctx.guild.voice_client

    if vc is None or not state["queue"]:
        return

    title, make_source = state["queue"].pop(0)
    source = make_source()

    def after_playing(error):
        if error:
            print("Playback error:", error)

        if state["loop"]:
            state["queue"].append((title, make_source))

        ctx.bot.loop.call_soon_threadsafe(play_next, ctx)

    vc.play(source, after=after_playing)


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


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        vc = member.guild.voice_client
        if vc and len(vc.channel.members) == 1:
            state = get_state(self.bot, member.guild.id)
            state["queue"].clear()
            vc.stop()
            await vc.disconnect()

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Join a voice channel first")
            return

        if ctx.voice_client is not None:
            await ctx.send("I'm already in a voice channel")
            return

        await ctx.author.voice.channel.connect()
        await ctx.send("Joined the voice channel")

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def leave(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("I'm not in a voice channel")
            return

        state = get_state(self.bot, ctx.guild.id)
        state["queue"].clear()
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel")

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def play(self, ctx, filename: str):
        if ctx.author.voice is None:
            await ctx.send("Join a voice channel first")
            return

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        path = os.path.join("../audio", filename)
        if not os.path.isfile(path):
            await ctx.send(f"File {filename} not found")
            return

        def make_local_source():
            return create_source(path)

        state = get_state(self.bot, ctx.guild.id)
        vc = ctx.voice_client
        item = (filename, make_local_source)

        if not vc.is_playing():
            state["queue"].insert(0, item)
            play_next(ctx)
            await ctx.send(f"Playing {filename}")
        else:
            state["queue"].append(item)
            await ctx.send(f"Queued {filename}")

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def playnow(self, ctx, filename: str):
        if ctx.author.voice is None:
            await ctx.send("Join a voice channel first")
            return

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        path = os.path.join("audio", filename)
        if not os.path.isfile(path):
            await ctx.send(f"File {filename} not found")
            return

        def make_local_source():
            return create_source(path)

        state = get_state(self.bot, ctx.guild.id)
        state["queue"].insert(0, (filename, make_local_source))

        vc = ctx.voice_client
        if vc.is_playing():
            vc.stop()
        else:
            play_next(ctx)

        await ctx.send(f"Playing {filename} now")

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def yt(self, ctx, *, query: str):
        if ctx.author.voice is None:
            await ctx.send("Join a voice channel first")
            return

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        video_id, title = get_youtube_audio(query)

        def make_yt_source():
            with yt_dlp.YoutubeDL({"format": "bestaudio", "quiet": True}) as ydl:
                info = ydl.extract_info(video_id, download=False)
                url = info["url"]

            return discord.FFmpegOpusAudio(
                executable="ffmpeg.exe",
                source=url,
                options="-vn",
                bitrate=128
            )

        state = get_state(self.bot, ctx.guild.id)
        vc = ctx.voice_client
        item = (title, make_yt_source)

        if not vc.is_playing():
            state["queue"].insert(0, item)
            play_next(ctx)
            await ctx.send(f"Playing **{title}**")
        else:
            state["queue"].append(item)
            await ctx.send(f"Queued **{title}**")

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc is None or not vc.is_playing():
            await ctx.send("Nothing is playing")
            return

        vc.stop()
        await ctx.send("Skipped current song")

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def stop(self, ctx, target: str = None):
        vc = ctx.voice_client
        if vc is None:
            await ctx.send("I'm not in a voice channel")
            return

        state = get_state(self.bot, ctx.guild.id)

        if target == "queue":
            state["queue"].clear()
            if vc.is_playing():
                vc.stop()
            await ctx.send("Stopped music and cleared queue")
        else:
            if vc.is_playing():
                vc.stop()
                await ctx.send("Stopped current song")
            else:
                await ctx.send("Nothing is playing")

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc is None or not vc.is_playing():
            await ctx.send("Nothing is playing")
            return

        vc.pause()
        await ctx.send("Paused")

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def resume(self, ctx):
        vc = ctx.voice_client
        if vc is None or not vc.is_paused():
            await ctx.send("Nothing is paused")
            return

        vc.resume()
        await ctx.send("Resumed")

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def queue(self, ctx):
        state = get_state(self.bot, ctx.guild.id)

        if not state["queue"]:
            await ctx.send("Queue is empty")
            return

        msg = "**Queue:**\n"
        for i, (title, _) in enumerate(state["queue"], start=1):
            msg += f"{i}. {title}\n"

        await ctx.send(msg)

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def volume(self, ctx, vol: int):
        global VOLUME

        if vol < 0 or vol > 200:
            await ctx.send("Volume must be between 0 and 200")
            return

        VOLUME = vol
        await ctx.send(f"Volume set to {vol}%")

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def list(self, ctx):
        audio_dir = "audio"

        if not os.path.isdir(audio_dir):
            await ctx.send("Audio folder not found")
            return

        files = [
            f for f in os.listdir(audio_dir)
            if f.lower().endswith((".mp3", ".wav", ".ogg", ".opus"))
        ]

        if not files:
            await ctx.send("No audio files found")
            return

        msg = "**Available songs:**\n" + "\n".join(f"- {f}" for f in files)
        await ctx.send(msg)

    @commands.command()
    @commands.check(music_channel_commands)
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, TRUSTED_MEMBER_ROLE_ID)
    async def loop(self, ctx):
        state = get_state(self.bot, ctx.guild.id)
        state["loop"] = not state["loop"]

        status = "🔁 **ON**" if state["loop"] else "⏹ **OFF**"
        await ctx.send(f"Loop mode is now {status}")


async def setup(bot):
    await bot.add_cog(Music(bot))
