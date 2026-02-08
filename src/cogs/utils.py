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
        self.afk_users = {}
        self.afk_nicks = {}


    @commands.command()
    @commands.check(command_channel)
    async def uptime(self, ctx):
        seconds = int(time.time() - self.bot.start_time)
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
                "`!botinfo`, `!cogs`\n"
                "`!id [@user]`, !afk [reason]`\n"
                "`!remind <scope> <time> <text>\n`"
            ),
            inline=False
        )

        # 🛠️ Moderation
        embed.add_field(
            name="🛠️ Moderation",
            value=(
                "`!kick @user [reason]`\n"
                "`!ban @user [reason]`\n"
                "`!timeout @user [minutes] [reason]`\n"
                "`!purge <amount> [@user]`\n"
                "`!slowmode <seconds>`\n"
                "`!lock`, `!unlock`"
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
                    "`!dm @user <message>`\n"
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




    @commands.command()
    async def afk(self, ctx, *, reason: str = "AFK"):
        member = ctx.author

        # Store reason + original nick
        self.afk_users[member.id] = reason
        self.afk_nicks[member.id] = member.nick  # None if user has no nickname

        # Build the new nick but avoid doubling if already has it
        base_name = member.display_name
        if base_name.startswith("💤 ") or (member.nick and member.nick.startswith("💤 ")):
            new_nick = member.nick or base_name
        else:
            new_nick = f"💤 {base_name}"

        # Permission checks
        can_manage = ctx.guild.me.guild_permissions.manage_nicknames
        is_owner = (member.id == ctx.guild.owner_id)
        higher_role_ok = ctx.guild.me.top_role.position > member.top_role.position

        nick_changed = False
        if not can_manage:
            # Tell owner/mods (or the user) that bot lacks permission
            await ctx.send("💤 AFK set — **I can't change your nickname** (missing Manage Nicknames permission).")
        elif is_owner:
            await ctx.send("💤 AFK set — I can't change the server owner's nickname, but AFK is active.")
        elif not higher_role_ok:
            await ctx.send("💤 AFK set — I can't change your nickname because your role is higher or equal to mine.")
        else:
            try:
                # Only try to set nick if it actually differs
                if member.nick != new_nick:
                    await member.edit(nick=new_nick)
                    nick_changed = True
            except discord.Forbidden:
                # fallback message
                await ctx.send("💤 AFK set — failed to change nickname (permission error).")
            except Exception as e:
                await ctx.send(f"💤 AFK set — unexpected error changing nick: `{e}`")

        # Final confirmation (if we haven't already informed about permission issues)
        if not (not can_manage or is_owner or not higher_role_ok):
            # if nothing was already sent, send a confirmation
            if not nick_changed:
                # either nick was already that or something else, but AFK active
                await ctx.send(f"💤 {member.mention} is now AFK: **{reason}**")
            else:
                await ctx.send(f"💤 {member.mention} is now AFK: **{reason}** (nickname updated)")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.author.id in self.afk_users and not message.content.startswith("!"):
            member = message.author

            self.afk_users.pop(member.id)
            original_nick = self.afk_nicks.pop(member.id, None)

            # restore nickname only if we previously saved one (could be None)
            try:
                # If original_nick is None, setting nick=None restores username.
                if original_nick != member.nick:
                    await member.edit(nick=original_nick)
            except discord.Forbidden:
                # can't restore — ignore but tell the user
                await message.channel.send("👋 Welcome back — AFK removed, but I couldn't restore your old nickname (permission).")
            except Exception:
                pass

            await message.channel.send(f"👋 Welcome back {member.mention}, AFK removed")

        for user_id, reason in self.afk_users.items():
            if f"<@{user_id}>" in message.content:
                await message.channel.send(
                    f"💤 <@{user_id}> is AFK: **{reason}**"
                )

    @commands.command()
    async def id(self, ctx, target: discord.Object = None):
        if target is None:
            await ctx.send(
                f"🆔 **Your ID:** `{ctx.author.id}`\n"
                f"🆔 **Channel ID:** `{ctx.channel.id}`\n"
                f"🆔 **Server ID:** `{ctx.guild.id}`"
            )
            return

        await ctx.send(f"🆔 **ID:** `{target.id}`")

    @commands.command()
    @commands.check(command_channel)
    async def whois(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(
            f"🧍 **{member.name}**\n"
            f"🆔 ID: `{member.id}`\n"
            f"📅 Joined: {member.joined_at.strftime('%d-%m-%Y')}"
        )

    @commands.command()
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(member.display_avatar.url)

    @commands.command()
    @commands.check(command_channel)
    async def poll(self, ctx, *, content: str):
        parts = [p.strip() for p in content.split("|")]

        if len(parts) < 3:
            return await ctx.send(
                "❌ Usage: `!poll Question | Option 1 | Option 2 [| Option 3...]`"
            )

        question = parts[0]
        options = parts[1:]

        if len(options) > 5:
            return await ctx.send("❌ Max **5** options allowed")

        emojis = ["🇦", "🇧", "🇨", "🇩", "🇪"]

        desc = "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))

        embed = discord.Embed(
            title="🗳️ Poll",
            description=f"**{question}**\n\n{desc}",
            color=0x00ffcc
        )
        embed.set_footer(text=f"Poll by {ctx.author}")

        msg = await ctx.send(embed=embed)

        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

    @commands.command()
    @commands.has_role(OWNER_ROLE_ID)
    async def dm(self, ctx, member: discord.Member = None, *, message: str = None):
        if member is None or message is None:
            return await ctx.send("❌ Usage: `!dm @user <message>`")

        try:
            await ctx.message.delete()
            await member.send(
                f"📩 **Message from {ctx.guild.name}**\n"
                f"👤 Sent by: {ctx.author}\n\n"
                f"{message}"
            )
            await ctx.send(f"✅ DM sent to **{member}**")
        except discord.Forbidden:
            await ctx.send("❌ I can't DM this user (DMs closed or blocked)")

    @commands.command()
    @commands.check(command_channel)
    async def remind(self, ctx, scope: str, time: str, *, reminder: str):
        scope = scope.lower()
        if scope not in ("global", "personal"):
            return await ctx.send("❌ Scope must be `global` or `personal`")

        unit = time[-1]
        if unit not in ("s", "m", "h"):
            return await ctx.send("❌ Time must end with `s`, `m`, or `h`")

        try:
            value = int(time[:-1])
        except ValueError:
            return await ctx.send("❌ Invalid time format")

        seconds = value
        if unit == "m":
            seconds *= 60
        elif unit == "h":
            seconds *= 3600

        if seconds <= 0 or seconds > 86400:
            return await ctx.send("❌ Time must be between **1s and 24h**")

        await ctx.send(
            f"⏰ Alright {ctx.author.mention}, I’ll remind you in **{time}** ({scope})"
        )

        await asyncio.sleep(seconds)

        msg = f"🔔 **Reminder:** {reminder}"

        if scope == "global":
            await ctx.send(f"{ctx.author.mention} {msg}")
        else:
            try:
                await ctx.author.send(msg)
            except discord.Forbidden:
                await ctx.send("❌ I couldn't DM you (DMs are closed)")
            



async def setup(bot):
    await bot.add_cog(Utils(bot))
