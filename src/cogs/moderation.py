import discord
from discord.ext import commands
from datetime import timedelta
from config import OWNER_ROLE_ID, MOD_ROLE_ID, ADIN_ROLE_ID

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

async def setup(bot):
    await bot.add_cog(Moderation(bot))
