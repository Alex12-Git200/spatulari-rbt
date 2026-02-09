import discord
from discord.ext import commands
import json
import time
import random
from config import LEVELS_FILE, TRUSTED_MEMBER_ROLE_ID


class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_cooldowns = {}
        self.levels = self.load_levels()

    def load_levels(self):
        try:
            with open(LEVELS_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_levels(self):
        with open(LEVELS_FILE, "w") as f:
            json.dump(self.levels, f, indent=4)


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = str(message.author.id)
        now = time.time()

        # cooldown: 60s
        if user_id in self.user_cooldowns and now - self.user_cooldowns[user_id] < 60:
            return

        self.user_cooldowns[user_id] = now

        # init user
        if user_id not in self.levels:
            self.levels[user_id] = {"xp": 0, "level": 1}

        xp_gain = random.randint(15, 25)
        self.levels[user_id]["xp"] += xp_gain

        lvl = self.levels[user_id]["level"]
        xp_needed = lvl * 100

        # level up
        if self.levels[user_id]["xp"] >= xp_needed:
            self.levels[user_id]["level"] += 1
            self.levels[user_id]["xp"] = 0
            new_level = self.levels[user_id]["level"]

            await message.channel.send(
                f"🎉 {message.author.mention} just hit **Level {new_level}**!"
            )

            # trusted role unlock
            if new_level == 15:
                role = message.guild.get_role(TRUSTED_MEMBER_ROLE_ID)
                if role and role not in message.author.roles:
                    try:
                        await message.author.add_roles(role)
                        await message.channel.send(
                            f"🛡️ {message.author.mention} unlocked **Trusted Member**!"
                        )
                    except discord.Forbidden:
                        pass

        self.save_levels()

    @commands.command()
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)

        if user_id not in self.levels:
            return await ctx.send("No rank data yet. Start chatting!")

        data = self.levels[user_id]
        needed = data["level"] * 100

        await ctx.send(
            f"📊 **{member.name}**\n"
            f"Level: **{data['level']}**\n"
            f"XP: **{data['xp']}/{needed}**"
        )

    @commands.command()
    async def leaderboard(self, ctx):
        sorted_users = sorted(
            self.levels.items(),
            key=lambda x: (x[1]["level"], x[1]["xp"]),
            reverse=True
        )

        msg = "🏆 **Top Chatters**\n"
        for i, (uid, data) in enumerate(sorted_users[:5], 1):
            user = self.bot.get_user(int(uid))
            name = user.name if user else "Unknown"
            msg += f"{i}. **{name}** — Level {data['level']}\n"

        await ctx.send(msg)


async def setup(bot):
    await bot.add_cog(XP(bot))
