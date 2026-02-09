import discord
from discord.ext import commands
from config import STATUS_CHANNEL_ID

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_message_id = None

    async def get_status_message(self):
        channel = self.bot.get_channel(STATUS_CHANNEL_ID)
        if not channel:
            return None

        # cached message
        if self.status_message_id:
            try:
                return await channel.fetch_message(self.status_message_id)
            except discord.NotFound:
                self.status_message_id = None

        # search pinned
        async for msg in channel.pins():
            if msg.author == self.bot.user:
                self.status_message_id = msg.id
                return msg

        # create new
        embed = discord.Embed(
            title="🤖 Bot Status",
            description="🟡 Starting up...",
            color=0xffff00
        )
        msg = await channel.send(embed=embed)
        await msg.pin()
        self.status_message_id = msg.id
        return msg

    async def update_status(self, state: str):
        msg = await self.get_status_message()
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


async def setup(bot):
    await bot.add_cog(Status(bot))
