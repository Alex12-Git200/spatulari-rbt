import discord
from discord.ext import commands, tasks
import feedparser
from config import *

class YouTube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = YT_ANNOUNCE_CHANNEL_ID
        self.last_video_id = None
        self.rss_url = "https://www.youtube.com/feeds/videos.xml?channel_id=UCFVnjoLRjhiBJxkYNXUePjQ"

    def get_latest_video(self):
        feed = feedparser.parse(self.rss_url)
        if not feed.entries:
            return None

        entry = feed.entries[0]
        return {
            "title": entry.title,
            "url": entry.link
        }

    @tasks.loop(minutes=5)
    async def check_youtube(self):
        video = self.get_latest_video()
        if not video:
            return

        if video["url"] == self.last_video_id:
            return

        self.last_video_id = video["url"]

        channel = self.bot.get_channel(self.channel_id)
        if channel:
            await channel.send(
                f"📢 @everyone **New YouTube video!**\n"
                f"🎬 **{video['title']}**\n"
                f"🔗 {video['url']}"
            )

    @check_youtube.before_loop
    async def before_check_youtube(self):
        await self.bot.wait_until_ready()
        video = self.get_latest_video()
        if video:
            self.last_video_id = video["url"]

    @commands.command()
    @commands.has_role(OWNER_ROLE_ID)
    async def testytpost(self, ctx):
        video = self.get_latest_video()
        if not video:
            return await ctx.send("❌ No videos found.")

        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return await ctx.send("❌ Announce channel not found.")

        await channel.send(
            f"🧪 **TEST: New YouTube video!**\n"
            f"🎬 **{video['title']}**\n"
            f"🔗 {video['url']}"
        )

        await ctx.send("✅ Test YouTube post sent.")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_youtube.is_running():
            self.check_youtube.start()

async def setup(bot):
    await bot.add_cog(YouTube(bot))
