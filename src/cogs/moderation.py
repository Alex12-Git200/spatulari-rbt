import discord
from discord.ext import commands
from datetime import timedelta
from config import OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID, MY_USER_ID


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    async def notify_owner(self, text: str):
        owner = await self.bot.fetch_user(MY_USER_ID)
        if owner:
            try:
                await owner.send(f"⚠️ **Bot Alert:** {text}")
            except discord.Forbidden:
                print(f"Failed to DM owner: {text}")

    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if member == ctx.author:
            await ctx.send("You can't kick yourself")
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("🚫 You can't moderate someone with an equal/higher role")
            return
        await member.kick(reason=reason)
        await ctx.send(f"👢 Kicked {member.mention}\n📄 Reason: {reason}")

    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if member == ctx.author:
            await ctx.send("You can't ban yourself")
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("🚫 You can't moderate someone with an equal/higher role")
            return
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Banned {member.mention}\n📄 Reason: {reason}")

    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID)
    async def timeout(self, ctx, member: discord.Member, minutes: int = 10, *, reason="No reason provided"):
        if member == ctx.author:
            await ctx.send("You can't timeout yourself")
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.send("🚫 You can't moderate someone with an equal/higher role")
            return
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(
            f"⏳ Timed out {member.mention} for **{minutes} minutes**\n📄 Reason: {reason}"
        )

    @kick.error
    @ban.error
    @timeout.error
    async def mod_error(self, ctx, error):
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("❌ You don't have permission to do that")

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
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID)
    async def slowmode(self, ctx, seconds: int = None):
        if seconds is None:
            await ctx.send("❌ Usage: `!slowmode <seconds>` or `!slowmode 0`")
            return

        if seconds < 0 or seconds > 21600:
            await ctx.send("❌ Slowmode must be between **0 and 21600** seconds")
            return

        await ctx.channel.edit(slowmode_delay=seconds)

        if seconds == 0:
            await ctx.send("🚀 Slowmode **disabled**")
        else:
            await ctx.send(f"🐢 Slowmode set to **{seconds}s**")

    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID)
    async def lock(self, ctx):
        role = ctx.guild.default_role
        await ctx.channel.set_permissions(role, send_messages=False)
        await ctx.send("🔒 Channel locked")

    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID)
    async def unlock(self, ctx):
        role = ctx.guild.default_role
        await ctx.channel.set_permissions(role, send_messages=True)
        await ctx.send("🔓 Channel unlocked")


    @commands.command()
    @commands.has_any_role(OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID)
    async def purge(self, ctx, amount: int, member: discord.Member = None):
        if amount <= 0 or amount > 100:
            await ctx.send("❌ Amount must be between **1 and 100**")
            return

        messages = []

        async for msg in ctx.channel.history(limit=amount + 1):
            if member:
                if msg.author == member:
                    messages.append(msg)
            else:
                messages.append(msg)

        if not messages:
            await ctx.send("⚠️ No messages found to delete", delete_after=3)
            return

        await ctx.channel.delete_messages(messages)

        await ctx.send(
            f"🧹 Deleted **{len(messages)-1}** message(s)"
            + (f" from **{member.display_name}**" if member else ""),
            delete_after=3
        )

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Usage: `!purge <amount> [@user]`")
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.send("❌ You don’t have permission to use this")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid arguments")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
