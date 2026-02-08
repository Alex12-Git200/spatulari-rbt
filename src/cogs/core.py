from discord.ext import commands
from config import OWNER_ROLE_ID

PROTECTED_EXTENSIONS = {
    "cogs.core",
}

UNLOAD_ORDER = [
    "cogs.fun",
    "cogs.moderation",
    "cogs.music",
    "cogs.utils",
]

LOAD_ORDER = [
    "cogs.utils",
    "cogs.moderation",
    "cogs.fun",
    "cogs.music",
]


class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(OWNER_ROLE_ID)
    async def unload(self, ctx, ext: str):
        if ext in PROTECTED_EXTENSIONS:
            return await ctx.send("🚫 That extension is protected")

        if ext not in self.bot.extensions:
            return await ctx.send(f"⚠️ `{ext}` is not loaded")

        await self.bot.unload_extension(ext)
        await ctx.send(f"🧹 Unloaded `{ext}` ✅")

    @commands.command()
    @commands.has_role(OWNER_ROLE_ID)
    async def load(self, ctx, ext: str):
        if ext in self.bot.extensions:
            return await ctx.send(f"⚠️ `{ext}` is already loaded")

        await self.bot.load_extension(ext)
        await ctx.send(f"📦 Loaded `{ext}` ✅")

    @commands.command()
    @commands.has_role(OWNER_ROLE_ID)
    async def loadall(self, ctx):
        report = []

        for ext in LOAD_ORDER:
            if ext in self.bot.extensions:
                report.append(f"⚠️ {ext} already loaded")
                continue

            try:
                await self.bot.load_extension(ext)
                report.append(f"📦 Loaded {ext}")
            except Exception as e:
                report.append(f"❌ {ext}: `{type(e).__name__}: {e}`")

        await ctx.send("\n".join(report))

    @commands.command()
    @commands.has_role(OWNER_ROLE_ID)
    async def unloadall(self, ctx):
        report = []

        for ext in UNLOAD_ORDER:
            if ext in PROTECTED_EXTENSIONS:
                report.append(f"🚫 {ext} protected")
                continue

            if ext not in self.bot.extensions:
                report.append(f"⚠️ {ext} not loaded")
                continue

            try:
                await self.bot.unload_extension(ext)
                report.append(f"🧹 Unloaded {ext}")
            except Exception as e:
                report.append(f"❌ {ext}: `{type(e).__name__}: {e}`")

        await ctx.send("\n".join(report))

    @commands.command()
    @commands.has_role(OWNER_ROLE_ID)
    async def reloadall(self, ctx):
        failed = []
        for ext in list(self.bot.extensions):
            try:
                await self.bot.reload_extension(ext)
            except:
                failed.append(ext)

        if failed:
            await ctx.send(f"⚠️ Failed to reload:\n```{failed}```")
        else:
            await ctx.send("🔄 All cogs reloaded ✅")

async def setup(bot):
    await bot.add_cog(Core(bot))
