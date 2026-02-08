from discord.ext import commands
import random
import discord
from config import COMMANDS_CHANNEL_ID, TRUSTED_MEMBER_ROLE_ID
from utils.checks import command_channel

def trusted_or_staff(ctx):
    return (
        any(role.id == TRUSTED_MEMBER_ROLE_ID for role in ctx.author.roles)
        or ctx.author.guild_permissions.manage_messages
    )

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(command_channel)
    async def coinflip(self, ctx):
        await ctx.send(f"🪙 Coinflip: **{random.choice(['Heads', 'Tails'])}**")

    @commands.command()
    @commands.check(command_channel)
    async def dice(self, ctx):
        await ctx.send(f"🎲 You rolled a **{random.randint(1, 6)}**")

    @commands.command()
    @commands.check(command_channel)
    async def eightball(self, ctx, *, question: str = None):
        if question is None:
            await ctx.send("🎱 Ask me a question first")
            return

        responses = [
            "Yes 😎", "No", "Maybe 👀", "Absolutely 🔥",
            "Ask again later 💤", "Nah chief ❌"
        ]
        await ctx.send(f"🎱 **{random.choice(responses)}**")

    @commands.command()
    @commands.check(trusted_or_staff)
    async def say(self, ctx, *, msg: str):
        await ctx.message.delete()
        await ctx.send(msg)


    @commands.command()
    @commands.check(command_channel)
    async def slap(self, ctx, member: discord.Member):
        await ctx.send(f"👊 {ctx.author.mention} slapped {member.mention}")

    @commands.command()
    @commands.check(command_channel)
    async def rate(self, ctx, *, thing: str):
        score = random.randint(0, 10)
        await ctx.send(f"📈 I rate **{thing}** a **{score}/10**")

    
    @commands.command()
    @commands.check(command_channel)
    async def touchgrass(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(f"{member.mention} go outside. Touch some grass. 🌱")

    @commands.command()
    @commands.check(command_channel)
    async def whois(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        await ctx.send(
            f"🧍 **{member.name}**\n"
            f"🆔 ID: `{member.id}`\n"
            f"📅 Joined: {member.joined_at.strftime('%d-%m-%Y')}"
        )


async def setup(bot):
    await bot.add_cog(Fun(bot))

