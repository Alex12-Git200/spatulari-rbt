import discord
from discord.ext import commands
import time
from config import *
from utils.checks import command_channel
import asyncio
import sys


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command()
    @commands.check(command_channel)
    async def uptime(self, ctx):
        seconds = int(time.time() - self.start_time)
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        await ctx.send(f"⏱️ Uptime: **{hours}h {mins}m {secs}s**")

    @commands.command()
    @commands.check(command_channel)
    async def serverinfo(self, ctx):
        g = ctx.guild
        await ctx.send(
            f"🏰 **{g.name}**\n"
            f"👥 Members: {g.member_count}\n"
            f"📅 Created: {g.created_at.strftime('%Y-%m-%d')}"
        )

    @commands.command()
    @commands.check(command_channel)
    async def help(self, ctx):
        embed = discord.Embed(
            title="🤖 Bot Help",
            description="Here’s what I can do 👇",
            color=0x00ffcc
        )

        # 🎵 Music
        embed.add_field(
            name="🎵 Music Commands",
            value=(
                "`!join`, `!leave`\n"
                "`!play <file>` · `!playnow <file>`\n"
                "`!yt <query>`\n"
                "`!pause`, `!resume`, `!skip`\n"
                "`!stop [queue]`\n"
                "`!queue`, `!loop`, `!volume <0-200>`, `!list`"
            ),
            inline=False
        )

        # 📈 Leveling
        embed.add_field(
            name="📈 Leveling",
            value=(
                "`!rank [@user]` · Check level & XP\n"
                "`!leaderboard` · Top chatters\n"
                "💡 *Level **15** unlocks **Trusted Member***"
            ),
            inline=False
        )

        # 🎲 Fun
        embed.add_field(
            name="🎲 Fun Commands",
            value=(
                "`!coinflip`, `!dice`\n"
                "`!eightball <question>`\n"
                "`!rate <thing>`\n"
                "`!slap @user`\n"
                "`!touchgrass [@user]`\n"
                "`!say <message>` *(trusted/staff)*"
            ),
            inline=False
        )

        # ℹ️ Info
        embed.add_field(
            name="ℹ️ Info Commands",
            value=(
                "`!about`, `!uptime`, `!ping`\n"
                "`!serverinfo`, `!whois [@user]`\n"
                "`!botinfo`, `!cogs`, `!extensions`"
            ),
            inline=False
        )

        # 🛠️ Moderation
        embed.add_field(
            name="🛠️ Moderation",
            value=(
                "`!kick @user [reason]`\n"
                "`!ban @user [reason]`\n"
                "`!timeout @user [minutes] [reason]`"
            ),
            inline=False
        )

        # 👑 Owner / Core
        if ctx.author.id == MY_USER_ID:
            embed.add_field(
                name="👑 Owner / Core",
                value=(
                    "`!load <cog>` · `!unload <cog>`\n"
                    "`!reload <cog>`\n"
                    "`!loadall` · `!unloadall`\n"
                    "`!restart`, `!exit`"
                ),
                inline=False
            )

        embed.set_footer(
            text=f"Requested by {ctx.author.name} | Built by Spatulari 🧠"
        )

        await ctx.send(embed=embed)


    @commands.command()
    @commands.has_role(OWNER_ROLE_ID)
    async def reload(self, ctx, extension: str):
        try:
            await self.bot.unload_extension(extension)

            await self.bot.load_extension(extension)
            await asyncio.sleep(2)
            await ctx.send(f"🔄 Reloaded `{extension}` ✅")
        except commands.ExtensionNotLoaded:
            await ctx.send(f"⚠️ `{extension}` is not loaded")
        except commands.ExtensionNotFound:
            await ctx.send(f"❌ `{extension}` not found")
        except Exception as e:
            await ctx.send(f"💥 Reload failed:\n```{e}```")

    @commands.command()
    @commands.check(command_channel)
    async def botinfo(self, ctx):
        await ctx.send(
            f"🤖 **Bot Info**\n"
            f"🧠 Python: {sys.version.split()[0]}\n"
            f"📦 discord.py: {discord.__version__}\n"
            f"📂 Loaded cogs: {len(self.bot.extensions)}\n"
            f"🧑‍💻 Github: https://github.com/spatulari/spatulari-rbt"
        )

    @commands.command()
    @commands.check(command_channel)
    async def ping(self, ctx):
        ws_latency = round(self.bot.latency * 1000)

        before = time.perf_counter()
        msg = await ctx.send("🏓 Pinging...")
        after = time.perf_counter()

        api_latency = round((after - before) * 1000)

        await msg.edit(
            content=(
                f"🏓 **Pong!**\n"
                f"📡 WS latency: **{ws_latency}ms**\n"
                f"⚡ API latency: **{api_latency}ms**"
            )
        )

    @commands.command()
    @commands.has_role(OWNER_ROLE_ID)
    async def cogs(self, ctx):
        cogs = "\n".join(self.bot.cogs.keys())
        await ctx.send(f"🧩 Loaded cogs:\n```{cogs}```")


async def setup(bot):
    await bot.add_cog(Utils(bot))
