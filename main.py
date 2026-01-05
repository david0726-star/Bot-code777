import os
import discord
import json
import asyncio
import time
import random
from discord.ext import commands
from datetime import datetime, timedelta
from keep_alive import keep_alive
from discord import app_commands

keep_alive()

# ---------------- BOT SETUP ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

GUILD_ID = 1432944752457809942  # Your server ID
guild = discord.Object(id=GUILD_ID)

# ---------------- BOT SETUP ----------------
class MyBot(commands.Bot):
    def __init__(self):
            super().__init__(
                command_prefix="!",
                intents=intents,
                application_id=1450834238843912233
            )

    async def setup_hook(self):
        await self.tree.sync(guild=guild)
        print("✅ Slash commands synced")

bot = MyBot()

# ---------------- JSON HELPERS ----------------
POINT_MULTIPLIER = 1
BOOST_ACTIVE = False
VIP_ROLE_NAME = "VIP"  # Change this to your server's actual VIP role name
PURCHASE_HISTORY_FILE = "purchase_history.json"
DATA_FILE = "points.json"
AFK_FILE = "afk.json"
WARNINGS_FILE = "warnings.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f: json.dump({}, f)
    with open(DATA_FILE, "r") as f: return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

def ensure_user(data, user_id):
    if user_id not in data:
        data[user_id] = {"points": 0, "last_daily": 0}

def load_afk():
    if not os.path.exists(AFK_FILE):
        with open(AFK_FILE, "w") as f: json.dump({}, f)
    with open(AFK_FILE, "r") as f: return json.load(f)

def save_afk(data):
    with open(AFK_FILE, "w") as f: json.dump(data, f, indent=4)

def load_warnings():
    if os.path.exists(WARNINGS_FILE):
        try: return json.load(open(WARNINGS_FILE))
        except: print("⚠️ Corrupted warnings.json")
    return {}

def save_warnings():
    with open(WARNINGS_FILE, "w") as f: json.dump(warnings_data, f, indent=2)
# --- Helper functions for purchase history ---
def load_purchase_history():
    if not os.path.exists(PURCHASE_HISTORY_FILE):
        with open(PURCHASE_HISTORY_FILE, "w") as f:
            json.dump({}, f)
    with open(PURCHASE_HISTORY_FILE, "r") as f:
        return json.load(f)

def save_purchase_history(history):
    with open(PURCHASE_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

warnings_data = load_warnings()

# ---------------- CONSTANTS ----------------
WELCOME_CHANNEL_ID = 1448132455172145315
POINT_CHANNEL_ID =1432944755951534122
DAILY_AMOUNT = 3
DAILY_COOLDOWN = 86400  # 24 hours

REWARDS = {
    "vip": {"name": "VIP Role", "price": 300, "description": "Get the VIP role automatically!"},
    "customcommand": {"name": "Custom Bot Command", "price": 400, "description": "Get your own custom bot command"},
    "trialmod": {"name": "Trial Mod (3 Days)", "price": 1000, "description": "Trial moderator for 3 days"},
    "custompfp": {"name": "Custom Bot PFP", "price": 500, "description": "Purchase this and open a ticket to customize the bot's profile picture!"}
}
invites_cache = {}

gif_files = {
    "shadow sucks": "DiscordBot/yousuck.gif",
    "shadow is og": "DiscordBot/yes.gif",
    "godgamer is cool": "DiscordBot/yes.gif",
    "w": "DiscordBot/w-arknights.gif",
    "troll": "DiscordBot/images.jpg",
    "67": "DiscordBot/sixseven.gif",
    "lol": "DiscordBot/lol.gif",
    "yes": "DiscordBot/yes.gif",
    "no": "DiscordBot/no.gif",
    "idk": "DiscordBot/idk.gif",
    "nerd": "DiscordBot/nerd.gif",
    "pls": "DiscordBot/pls.gif",
    "thank you bot": "DiscordBot/youwelcome.gif",
    "loser": "DiscordBot/loser.jpg",
    "thank you kevin": ["DiscordBot/salute.gif", "DiscordBot/ty.gif"],
}
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        count = member.guild.member_count
        file = discord.File("./DiscordBot/w-arknights.gif", filename="welcome.gif")
        await channel.send(f"🎉 Welcome {member.mention} to {member.guild.name}! You are our {count}th member! 🥳🎊", file=file)

    guild = member.guild
    if guild.id not in invites_cache:
        invites_cache[guild.id] = {}
    old_invites = invites_cache[guild.id]
    new_invites = await guild.invites()
    used_invite = None
    for invite in new_invites:
        if invite.code in old_invites and invite.uses > old_invites[invite.code]:
            used_invite = invite
            break
        elif invite.code not in old_invites and invite.uses > 0:
            used_invite = invite
            break
    invites_cache[guild.id] = {invite.code: invite.uses for invite in new_invites}

    if used_invite and used_invite.inviter:
        data = load_data()
        uid = str(used_invite.inviter.id)
        ensure_user(data, uid)
        data[uid]["points"] += 100
        save_data(data)
        try:
            await used_invite.inviter.send(f"🎉 You earned 100 points because {member.display_name} joined using your invite!")
        except:
            pass

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        count = member.guild.member_count
        file = discord.File("./DiscordBot/loser.jpg", filename="leave.gif")
        await channel.send(f"👋 {member.name} left the server. We are now {count} members. 😢", file=file)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    user_id = str(message.author.id)

    # ---- AFK removal ----
    data_afk = load_afk()
    if user_id in data_afk:
        del data_afk[user_id]
        save_afk(data_afk)
        await message.channel.send(f"✅ Welcome back {message.author.mention}, your AFK has been removed!")

    # ---- AFK mentions ----
    for user in message.mentions:
        uid = str(user.id)
        if uid in data_afk:
            await message.channel.send(f"ℹ️ {user.display_name} is currently AFK: {data_afk[uid]}")

    # ---- Points collection ----
    if message.channel.id == POINT_CHANNEL_ID:
        data_points = load_data()
        ensure_user(data_points, user_id)

        data_points[user_id]["points"] += POINT_MULTIPLIER
        save_data(data_points)
    # ---- GIF triggers ----
    content = message.content.lower().strip()
    for key, gif in gif_files.items():
        if content == key.lower():
            file_path = random.choice(gif) if isinstance(gif, list) else gif
            await message.channel.send(file=discord.File(file_path))
            break

    # ---- Process commands ----
    await bot.process_commands(message)

# ---------------- PREFIX COMMANDS ----------------
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.name}!")

@bot.tree.command(name="points", description="Check points")
@app_commands.guilds(guild)
async def points(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = load_data()
    pts = data.get(str(member.id), {}).get("points", 0)
    await interaction.response.send_message(
        f"💬 **{member.display_name}** has **{pts} W Chat Points**"
    )

@bot.tree.command(name="givepoints", description="Give points to a member")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.guilds(guild)
async def givepoints(interaction: discord.Interaction, member: discord.Member, amount: int):
    data = load_data()
    ensure_user(data, str(member.id))
    data[str(member.id)]["points"] += amount
    save_data(data)
    await interaction.response.send_message(
        f"✅ Gave **{amount} W Chat Points** to {member.mention}"
    )
@bot.tree.command(name="removepoints", description="Remove points from a member")
@app_commands.guilds(guild)
async def removepoints(interaction: discord.Interaction, member: discord.Member, amount: int):
    data = load_data()
    ensure_user(data, str(member.id))
    data[str(member.id)]["points"] = max(data[str(member.id)]["points"] - amount, 0)
    save_data(data)
    await interaction.response.send_message(
        f"✅ Removed **{amount} W Chat Points** from {member.mention}"
    )
@bot.tree.command(name="leaderboard", description="Show top points leaderboard")
@app_commands.guilds(guild)
async def leaderboard(interaction: discord.Interaction):
    data = load_data()
    if not data:
        return await interaction.response.send_message("❌ No data yet.")

    sorted_users = sorted(data.items(), key=lambda x: x[1]["points"], reverse=True)
    embed = discord.Embed(title="🏆 W Chat Leaderboard", color=discord.Color.gold())

    for i, (uid, info) in enumerate(sorted_users[:10], start=1):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else "User Left"
        embed.add_field(
            name=f"{i}. {name}",
            value=f"{info['points']} points",
            inline=False
        )

    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="daily", description="Claim daily points")
@app_commands.guilds(guild)
async def daily(interaction: discord.Interaction):
    data = load_data()
    uid = str(interaction.user.id)
    ensure_user(data, uid)

    now = int(time.time())
    last = data[uid]["last_daily"]

    if now - last >= DAILY_COOLDOWN:
        data[uid]["points"] += DAILY_AMOUNT
        data[uid]["last_daily"] = now
        save_data(data)
        await interaction.response.send_message(
            f"🎁 You received **{DAILY_AMOUNT} W Chat Points**!"
        )
    else:
        remaining = DAILY_COOLDOWN - (now - last)
        h, m = remaining // 3600, (remaining % 3600) // 60
        await interaction.response.send_message(
            f"⏳ Already claimed. Try again in **{h}h {m}m**."
        )

@bot.tree.command(name="shop", description="View the reward shop")
@app_commands.guilds(guild)
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 W Chat Reward Shop",
        description="Use `/buy <item>`",
        color=discord.Color.green()
    )
    for key, r in REWARDS.items():
        embed.add_field(
            name=f"{r['name']} — {r['price']} points",
            value=f"ID: `{key}`\n{r['description']}",
            inline=False
        )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(
    name="buy",
    description="Buy an item from the shop"
)
@app_commands.choices(
        item=[
            app_commands.Choice(name="VIP Role", value="vip"),
            app_commands.Choice(name="Custom Command", value="customcommand"),
            app_commands.Choice(name="Trial Mod (3 Days)", value="trialmod"),
            app_commands.Choice(name="Custom Bot PFP", value="custompfp")
        ]
)
@app_commands.guilds(guild)
async def buy(interaction: discord.Interaction, item: app_commands.Choice[str]):
    """Buy a shop item selected from a dropdown."""

    data = load_data()
    uid = str(interaction.user.id)
    ensure_user(data, uid)

    reward = REWARDS[item.value]
    if data[uid]["points"] < reward["price"]:
        return await interaction.response.send_message(
            f"❌ You need **{reward['price']} points**. You have **{data[uid]['points']}**.",
            ephemeral=True
        )

    # Deduct points
    data[uid]["points"] -= reward["price"]
    save_data(data)

    # -------------------- FIXED INDENTATION --------------------
    role_msg = ""

    if item.value == "vip":
        role = discord.utils.get(interaction.guild.roles, name=VIP_ROLE_NAME)
        if role:
            try:
                await interaction.user.add_roles(role)
                role_msg = f"✅ You received the **{VIP_ROLE_NAME}** role!"
            except discord.Forbidden:
                role_msg = "⚠️ I could not assign the role. Make sure my role is above VIP."
        else:
            role_msg = f"⚠️ Role **{VIP_ROLE_NAME}** not found in this server."

    elif item.value == "custompfp":
        role_msg = "📌 Please open a ticket and send the image to customize the bot's profile picture!"
    # ------------------------------------------------------------

    # Record purchase
    history = load_purchase_history()
    guild_id = str(interaction.guild.id)
    history.setdefault(guild_id, []).append({
        "user": f"{interaction.user} ({interaction.user.id})",
        "item": reward["name"],
        "points": reward["price"],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_purchase_history(history)

    await interaction.response.send_message(
        f"✅ Purchased **{reward['name']}** for {reward['price']} points. {role_msg}"
    )

@bot.command()
@commands.has_permissions(manage_guild=True)
async def purchases(ctx):
    """Show last 10 purchases for the server."""
    history = load_purchase_history()
    guild_id = str(ctx.guild.id)

    if guild_id not in history or not history[guild_id]:
        return await ctx.send("ℹ️ No purchases recorded for this server yet.")

    embed = discord.Embed(title=f"🛒 Purchase History for {ctx.guild.name}", color=discord.Color.blue())

    # Show last 10 purchases
    last_purchases = history[guild_id][-10:]
    for entry in reversed(last_purchases):
        embed.add_field(
            name=f"{entry['user']}",
            value=f"Item: {entry['item']}\nPoints Spent: {entry['points']}\nTime: {entry['time']}",
            inline=False
        )

    await ctx.send(embed=embed)
@bot.tree.command(name="gift", decription="gift other users item in the reward shop")
@app_commands.guilds(guild)
async def gift(context):
    last_purchase_history=load_purchase_history()
    if user_id=ctx.author.id:
    await interaction.response.send_message(
        f"what item do you want to gift?")
    
    

@bot.tree.command(name="boost", description="Start a 4x points boost")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.guilds(guild)
async def boost(interaction: discord.Interaction):
    global POINT_MULTIPLIER, BOOST_ACTIVE

    if BOOST_ACTIVE:
        return await interaction.response.send_message(
            "⚠️ A boost is already active!",
            ephemeral=True
        )

    POINT_MULTIPLIER = 4
    BOOST_ACTIVE = True

    channel = interaction.channel

    await channel.send(
        "@everyone 🔥 **4× POINT BOOST IS NOW ACTIVE!** 🔥\n"
        "Chat now to earn points faster!"
    )

    await interaction.response.send_message(
        "✅ 4× points boost started!"
    )
@bot.tree.command(name="endboost", description="End the points boost")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.guilds(guild)
async def endboost(interaction: discord.Interaction):
    global POINT_MULTIPLIER, BOOST_ACTIVE

    if not BOOST_ACTIVE:
        return await interaction.response.send_message(
            "⚠️ No boost is currently active.",
            ephemeral=True
        )

    POINT_MULTIPLIER = 1
    BOOST_ACTIVE = False

    await interaction.channel.send(
        "⏹️ **Point boost has ended.** Points are back to normal."
    )

    await interaction.response.send_message(
        "✅ Boost ended."
    )

@bot.tree.command(name="afk", description="Set your AFK status")
@app_commands.guilds(guild)
async def afk(interaction: discord.Interaction, reason: str = "AFK"):
    data = load_afk()
    data[str(interaction.user.id)] = reason
    save_afk(data)
    await interaction.response.send_message(
        f"✅ {interaction.user.mention} is now AFK: {reason}"
    )
@bot.tree.command(
    name="purchases",
    description="View the last 10 purchases in this server"
)
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.guilds(guild)
async def purchases(interaction: discord.Interaction):
    history = load_purchase_history()
    guild_id = str(interaction.guild.id)

    if guild_id not in history or not history[guild_id]:
        return await interaction.response.send_message(
            "ℹ️ No purchases recorded for this server yet.",
            ephemeral=True
        )

    embed = discord.Embed(
        title=f"🛒 Purchase History — {interaction.guild.name}",
        color=discord.Color.blue()
    )

    last_purchases = history[guild_id][-10:]

    for entry in reversed(last_purchases):
        embed.add_field(
            name=entry["user"],
            value=(
                f"**Item:** {entry['item']}\n"
                f"**Points Spent:** {entry['points']}\n"
                f"**Time:** {entry['time']}"
            ),
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# ---------------- MODERATION COMMANDS ----------------
# [Slash commands for warn, removewarn, checkwarnings, mute, unmute, kick, ban, unban, announce, addrole, removerole]
# Include all the slash commands exactly as in your original code
# ... (For brevity, paste your full slash commands here, properly indented)
# ---------------- MODERATION SLASH COMMANDS ----------------

# WARN
@bot.tree.command(name="warn", description="Warn a member")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guilds(guild)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    warnings_data.setdefault(guild_id, {}).setdefault(user_id, [])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    warnings_data[guild_id][user_id].append(f"[{timestamp}] {reason}")
    save_warnings()
    await interaction.response.send_message(f"⚠️ {member.mention} warned: {reason}")

# REMOVE WARN
@bot.tree.command(name="removewarn", description="Remove a warning")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guilds(guild)
async def removewarn(interaction: discord.Interaction, member: discord.Member, index: int = None):
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    if guild_id not in warnings_data or user_id not in warnings_data[guild_id] or not warnings_data[guild_id][user_id]:
        return await interaction.response.send_message(f"❌ {member.mention} has no warnings.", ephemeral=True)
    if index is None:
        warnings_data[guild_id][user_id] = []
        save_warnings()
        return await interaction.response.send_message(f"✅ All warnings removed for {member.mention}")
    user_warnings = warnings_data[guild_id][user_id]
    if 1 <= index <= len(user_warnings):
        removed = user_warnings.pop(index - 1)
        save_warnings()
        await interaction.response.send_message(f"✅ Removed warning #{index} for {member.mention}: {removed}")
    else:
        await interaction.response.send_message(f"❌ Invalid warning number.", ephemeral=True)

# CHECK WARNINGS
@bot.tree.command(name="checkwarnings", description="Check a member's warnings")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guilds(guild)
async def checkwarnings(interaction: discord.Interaction, member: discord.Member):
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    user_warnings = warnings_data.get(guild_id, {}).get(user_id, [])
    if not user_warnings:
        await interaction.response.send_message(f"ℹ️ {member.mention} has no warnings.")
    else:
        warnings_text = "\n".join([f"{i+1}. {w}" for i, w in enumerate(user_warnings)])
        await interaction.response.send_message(f"⚠️ Warnings for {member.mention}:\n{warnings_text}")

# MUTE
@bot.tree.command(name="mute", description="Mute a member (timeout)")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.guilds(guild)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason provided"):
    # Timeout the member
    await member.timeout(timedelta(minutes=minutes), reason=reason)
    
    # Google Form link
    form_url = "https://docs.google.com/forms/d/1QEZys41UEyubcov5jmhsq85LFPdhdlOw5Du71-iBjSw"
    
    # Attempt to DM the member
    try:
        await member.send(
            f"🔇 You have been muted in **{interaction.guild.name}** for {minutes} minutes.\n"
            f"Reason: {reason}\n\n"
            f"Please fill out this form: [Mute Form]({form_url})"
        )
        dm_status = "✅ DM sent to the member."
    except discord.Forbidden:
        dm_status = "⚠️ Could not DM the member (they may have DMs off)."
    
    # Send response in the channel
    await interaction.response.send_message(
        f"🔇 {member.mention} has been muted for {minutes} minutes.\n"
        f"Reason: {reason}\n{dm_status}"
    )


# UNMUTE
@bot.tree.command(name="unmute", description="Unmute a member")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.guilds(guild)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"🔊 {member.mention} unmuted.")

# KICK
@bot.tree.command(name="kick", description="Kick a member")
@app_commands.checks.has_permissions(kick_members=True)
@app_commands.guilds(guild)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 {member.mention} kicked.\nReason: {reason}")

@bot.tree.command(name="ban", description="Ban a member (DMs appeal form first)")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.guilds(guild)
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):
    appeal_link = "https://docs.google.com/forms/d/1QEZys41UEyubcov5jmhsq85LFPdhdlOw5Du71-iBjSw"

    # Try to DM the user BEFORE banning
    try:
        dm_embed = discord.Embed(
            title="🚫 You Have Been Banned",
            color=discord.Color.red()
        )
        dm_embed.add_field(name="Server", value=interaction.guild.name, inline=False)
        dm_embed.add_field(name="Reason", value=reason, inline=False)
        dm_embed.add_field(
            name="Appeal",
            value=f"You may appeal your ban here:\n{appeal_link}",
            inline=False
        )
        dm_embed.set_footer(text="Do not reply to this message.")

        await member.send(embed=dm_embed)
    except discord.Forbidden:
        # User has DMs closed — ignore safely
        pass
    except Exception as e:
        print(f"DM failed for {member}: {e}")

    # Ban the user
    await interaction.guild.ban(member, reason=reason)

    # Confirm to moderator
    await interaction.response.send_message(
        f"🔨 **{member}** has been banned.\n"
        f"📨 Appeal form was sent via DM (if possible).\n"
        f"📝 Reason: {reason}"
    )

# UNBAN
@bot.tree.command(name="unban", description="Unban a user by ID or name")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.guilds(guild)
async def unban(interaction: discord.Interaction, user_input: str):
    banned_users = [ban async for ban in interaction.guild.bans()]
    # Try ID
    if user_input.isdigit():
        uid = int(user_input)
        for ban_entry in banned_users:
            if ban_entry.user.id == uid:
                await interaction.guild.unban(ban_entry.user)
                return await interaction.response.send_message(f"♻️ {ban_entry.user} unbanned.")
    # Try name#discriminator or name
    matches = [ban.user for ban in banned_users if f"{ban.user.name}#{ban.user.discriminator}" == user_input or ban.user.name == user_input]
    if len(matches) == 1:
        await interaction.guild.unban(matches[0])
        await interaction.response.send_message(f"♻️ {matches[0]} unbanned.")
    elif len(matches) > 1:
        await interaction.response.send_message("❌ Multiple users found. Use ID.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ User not found in ban list.", ephemeral=True)

# ANNOUNCE
@bot.tree.command(name="announce", description="Send an announcement")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guilds(guild)
async def announce(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(f"# 📢 **{message}**")

# ---------------- ROLE MANAGEMENT ----------------
# ADD ROLE
@bot.tree.command(name="addrole", description="Add a role to a member")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.guilds(guild)
async def addrole(interaction: discord.Interaction, member: discord.Member, role_name: str):
    role_name = role_name.strip('"')
    roles = interaction.guild.roles
    role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), roles)
    if role is None:
        role = discord.utils.find(lambda r: role_name.lower() in r.name.lower(), roles)
    if role is None:
        return await interaction.response.send_message(f"❌ Role `{role_name}` not found.", ephemeral=True)
    if role >= interaction.guild.me.top_role:
        return await interaction.response.send_message("❌ I cannot assign a role higher than or equal to my top role.", ephemeral=True)
    try:
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ {role.name} has been added to {member.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I do not have permission to add this role.", ephemeral=True)

# REMOVE ROLE
@bot.tree.command(name="removerole", description="Remove a role from a member")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.guilds(guild)
async def removerole(interaction: discord.Interaction, member: discord.Member, role_name: str):
    role_name = role_name.strip('"')
    roles = interaction.guild.roles
    role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), roles)
    if role is None:
        role = discord.utils.find(lambda r: role_name.lower() in r.name.lower(), roles)
    if role is None:
        return await interaction.response.send_message(f"❌ Role `{role_name}` not found.", ephemeral=True)
    if role >= interaction.guild.me.top_role:
        return await interaction.response.send_message("❌ I cannot remove a role higher than or equal to my top role.", ephemeral=True)
    try:
        await member.remove_roles(role)
        await interaction.response.send_message(f"✅ {role.name} has been removed from {member.mention}.")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I do not have permission to remove this role.", ephemeral=True)
# ---------------- EVENTS ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.wait_until_ready()

    # Invite cache
    for g in bot.guilds:
        try:
            invites = await g.invites()
            invites_cache[g.id] = {invite.code: invite.uses for invite in invites}
        except discord.Forbidden:
            print(f"⚠️ Cannot fetch invites for {g.name} (missing permissions)")
    print("✅ Invite cache updated")
#clear/server info------------------------
@bot.tree.command(
    name="clear",
    description="Delete a number of messages from this channel"
)
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.guilds(guild)
async def clear(
    interaction: discord.Interaction,
    amount: int,
    user: discord.Member = None
):
    """
    Deletes `amount` messages in the current channel.
    If `user` is specified, deletes only messages from that user.
    """
    if amount < 1:
        return await interaction.response.send_message(
            "❌ Amount must be at least 1.", ephemeral=True
        )

    # Fetch messages
    def check(msg):
        return True if user is None else msg.author.id == user.id

    deleted = await interaction.channel.purge(limit=amount, check=check)
    await interaction.response.send_message(
        f"🧹 Deleted {len(deleted)} messages{' from ' + user.display_name if user else ''}.",
        ephemeral=True
    )
@bot.tree.command(
    name="serverinfo",
    description="Get information about this server"
)
@app_commands.guilds(guild)
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(
        title=f"📊 Server Info — {guild.name}",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    embed.add_field(name="Server Name", value=guild.name, inline=True)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=guild.owner, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
    embed.set_footer(text=f"Created • {guild.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    await interaction.response.send_message(embed=embed)

# ---------------- RUN BOT ----------------
bot.run(os.environ["DISCORD_BOT_TOKEN"])
