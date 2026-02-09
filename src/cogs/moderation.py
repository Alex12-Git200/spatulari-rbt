import discord
from discord.ext import commands
from datetime import timedelta
from config import OWNER_ROLE_ID, MOD_ROLE_ID, ADMIN_ROLE_ID, MY_USER_ID
from collections import deque
import time


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_times = deque()
        self.raid_threshold = 6
        self.raid_window = 1.5
        self.server_locked = False
        self.locked_join_attempts = []
        self.locked_overwrites = {}
        self.is_processing_lock = False
        self.locked_category_overwrites = {}


    async def notify_owner(self, text: str):
        owner = await self.bot.fetch_user(MY_USER_ID)
        if owner:
            try:
                await owner.send(f"⚠️ **Bot Alert:** {text}")
            except discord.Forbidden:
                print(f"Failed to DM owner: {text}")


    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADMIN_ROLE_ID)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if member == ctx.author:
            return await ctx.send("You can't kick yourself")
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("🚫 You can't moderate someone with an equal/higher role")

        await member.kick(reason=reason)
        await ctx.send(f"👢 Kicked {member.mention}\n📄 Reason: {reason}")


    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADMIN_ROLE_ID)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if member == ctx.author:
            return await ctx.send("You can't ban yourself")
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("🚫 You can't moderate someone with an equal/higher role")

        await member.ban(reason=reason)
        await ctx.send(f"🔨 Banned {member.mention}\n📄 Reason: {reason}")


    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADMIN_ROLE_ID)
    async def timeout(self, ctx, member: discord.Member, minutes: int = 10, *, reason="No reason provided"):
        if member == ctx.author:
            return await ctx.send("You can't timeout yourself")
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("🚫 You can't moderate someone with an equal/higher role")

        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(f"⏳ Timed out {member.mention} for **{minutes} minutes**\n📄 Reason: {reason}")


    @kick.error
    @ban.error
    @timeout.error
    async def mod_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("❌ You don't have permission")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Missing arguments")
        else:
            await ctx.send("💥 Something went wrong")
            await self.notify_owner(
                f"Moderation error in **{ctx.guild.name}**\n"
                f"Command: `{ctx.command}`\n"
                f"User: {ctx.author} ({ctx.author.id})\n"
                f"Error: `{type(error).__name__}: {error}`"
            )


    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADMIN_ROLE_ID)
    async def slowmode(self, ctx, seconds: int = None):
        if seconds is None:
            return await ctx.send("❌ Usage: `!slowmode <seconds>` or `!slowmode 0`")

        if seconds < 0 or seconds > 21600:
            return await ctx.send("❌ Slowmode must be between **0 and 21600** seconds")

        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send("🚀 Slowmode **disabled**" if seconds == 0 else f"🐢 Slowmode set to **{seconds}s**")


    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADMIN_ROLE_ID)
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel locked")


    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADMIN_ROLE_ID)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Channel unlocked")


    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADMIN_ROLE_ID)
    async def purge(self, ctx, amount: int, member: discord.Member = None):
        if amount <= 0 or amount > 100:
            return await ctx.send("❌ Amount must be between **1 and 100**")

        messages = []
        async for msg in ctx.channel.history(limit=amount + 1):
            if not member or msg.author == member:
                messages.append(msg)

        if not messages:
            return await ctx.send("⚠️ No messages found", delete_after=3)

        await ctx.channel.delete_messages(messages)
        await ctx.send(f"🧹 Deleted **{len(messages)-1}** message(s)", delete_after=3)


    @commands.command()
    @commands.has_role(OWNER_ROLE_ID)
    async def lockserver(self, ctx):
        if self.server_locked:
            return await ctx.send("⚠️ Server is already locked")

        self.server_locked = True
        self.is_processing_lock = True
        self.locked_overwrites.clear()

        everyone = ctx.guild.default_role

        for category in ctx.guild.categories:
            try:
                self.locked_category_overwrites[category.id] = category.overwrites_for(everyone)
                await category.set_permissions(everyone, connect=False, send_messages=False)
            except:
                pass

        for channel in ctx.guild.channels:
            try:
                self.locked_overwrites[channel.id] = channel.overwrites_for(everyone)
                await channel.set_permissions(everyone, send_messages=False, connect=False)
            except:
                pass

        for vc in ctx.guild.voice_channels:
            for member in vc.members:
                try:
                    await member.move_to(None)
                except:
                    pass

        self.is_processing_lock = False
        await ctx.send("🚨 **SERVER LOCKED** 🚨\nPermissions preserved.")


    @commands.command()
    @commands.has_role(OWNER_ROLE_ID)
    async def unlockserver(self, ctx):
        if not self.server_locked:
            return await ctx.send("⚠️ Server is not locked")

        self.server_locked = False
        everyone = ctx.guild.default_role

        for category in ctx.guild.categories:
            try:
                old = self.locked_category_overwrites.get(category.id)
                if old is not None:
                    await category.set_permissions(everyone, overwrite=old)
            except:
                pass

        self.locked_category_overwrites.clear()


        for channel in ctx.guild.channels:
            try:
                old = self.locked_overwrites.get(channel.id)

                if old is not None:
                    if isinstance(channel, discord.VoiceChannel):
                        old.connect = None
                        old.speak = None
                        old.stream = None

                    await channel.set_permissions(everyone, overwrite=old)

            except:
                pass

        self.locked_overwrites.clear()

        if self.locked_join_attempts:
            report = "\n".join(self.locked_join_attempts)
            final_report = (report[:1900] + "...") if len(report) > 1900 else report
            try:
                await ctx.author.send(f"📋 **Lockdown Join Attempts**\n```{final_report}```")
            except:
                await ctx.send("⚠️ Could not DM you the lockdown report.")

        self.locked_join_attempts.clear()
        self.join_times.clear()
    

        await ctx.send("🔓 **Server unlocked**\nPermissions restored.")


    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return

        now = time.monotonic()
        self.join_times.append(now)

        while self.join_times and now - self.join_times[0] > self.raid_window:
            self.join_times.popleft()

        if (
            len(self.join_times) >= self.raid_threshold
            and not self.server_locked
            and not self.is_processing_lock
        ):
            self.server_locked = True
            self.is_processing_lock = True

            everyone = member.guild.default_role
            self.locked_overwrites.clear()
            self.locked_category_overwrites.clear()

            for category in member.guild.categories:
                try:
                    self.locked_category_overwrites[category.id] = category.overwrites_for(everyone)
                    await category.set_permissions(everyone, connect=False, send_messages=False)
                except:
                    pass

            for channel in member.guild.channels:
                try:
                    self.locked_overwrites[channel.id] = channel.overwrites_for(everyone)
                    await channel.set_permissions(everyone, send_messages=False, connect=False)
                except:
                    pass

            self.join_times.clear()
            self.is_processing_lock = False

            try:
                await member.guild.owner.send(
                    "🚨 **AUTO LOCKDOWN TRIGGERED** 🚨\n"
                    f"Reason: **{self.raid_threshold} joins within {self.raid_window}s**"
                )
            except:
                pass

        if self.server_locked:
            if len(self.locked_join_attempts) < 100:
                self.locked_join_attempts.append(f"{member} ({member.id})")

            try:
                self.bot.loop.create_task(
                    member.send(
                        f"🚨 **Server Locked** 🚨\n"
                        f"You were banned from **{member.guild.name}** due to raid protection."
                    )
                )
            except:
                pass

            try:
                await member.ban(reason="Auto-lockdown: join raid")
            except:
                pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))
