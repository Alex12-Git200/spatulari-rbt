import discord
from discord.ext import commands
from config import WELCOME_CHANNEL_ID, MEMBER_ROLE_ID


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Member already gone (race condition safety)
        if not member.guild.get_member(member.id):
            return

        # Check lockdown state from Moderation cog
        mod_cog = self.bot.get_cog("Moderation")
        if mod_cog and getattr(mod_cog, "server_locked", False):
            print("🚫 Server locked — skipping welcome")
            return

        # --- Welcome message ---
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            try:
                await channel.send(
                    f"👋 Welcome {member.mention}! Enjoy your stay 😎"
                )
            except discord.Forbidden:
                print("❌ Missing permission to send welcome message")

        # --- DM welcome ---
        try:
            await member.send(
                "Welcome! Thanks for joining, don't break the rules 😄"
            )
        except discord.Forbidden:
            print("📭 DM blocked")

        # --- Auto role ---
        role = member.guild.get_role(MEMBER_ROLE_ID)
        if role and role not in member.roles:
            try:
                await member.add_roles(role)
            except discord.NotFound:
                print("⚠️ Member left before role could be added")
            except discord.Forbidden:
                print("❌ Missing permission to add role")


async def setup(bot):
    await bot.add_cog(Welcome(bot))
