#!/usr/bin/env python3
"""
NodeZero — Shadow Syndicate Discord Bot
One-command server setup: roles, channels, permissions, verification, rules.
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from pathlib import Path

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

DATA_FILE = Path(__file__).parent / "bot_data.json"

# ──────────────────────────────────────────────
# ROLE DEFINITIONS (order matters: lowest first)
# ──────────────────────────────────────────────

ROLES = [
    {
        "name": "Ghost",
        "color": discord.Color.dark_grey(),
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
    },
    {
        "name": "Operative",
        "color": discord.Color.from_rgb(45, 212, 191),  # teal
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
            add_reactions=True,
            use_external_emojis=True,
            connect=True,
            speak=True,
            stream=True,
            use_embedded_activities=True,
        ),
    },
    {
        "name": "Dark Pool Staker",
        "color": discord.Color.from_rgb(255, 176, 0),  # amber
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
    },
    {
        "name": "Night Raider",
        "color": discord.Color.from_rgb(192, 132, 252),  # purple
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
    },
    {
        "name": "Operator",
        "color": discord.Color.from_rgb(96, 165, 250),  # blue
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            kick_members=True,
            ban_members=True,
            manage_messages=True,
            mute_members=True,
            deafen_members=True,
            move_members=True,
            moderate_members=True,
        ),
    },
    {
        "name": "Syndicate Council",
        "color": discord.Color.from_rgb(192, 132, 252),  # purple
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            administrator=True,
        ),
    },
    {
        "name": "The Architect",
        "color": discord.Color.from_rgb(248, 250, 252),  # white
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            administrator=True,
        ),
    },
]

# ──────────────────────────────────────────────
# CATEGORY + CHANNEL DEFINITIONS
# ──────────────────────────────────────────────

# Each category has: name, channels list, and optional perms
# Channel types: "text", "voice", "announcement"
# "everyone_view" controls whether @everyone can see the category
# "operative_send" controls if Operatives can send messages (default True for text)
# Additional overrides can be specified

CATEGORIES = [
    # ── WELCOME ──
    {
        "name": "WELCOME & RULES",
        "everyone_view": True,
        "operative_send": False,  # read-only for Operatives too
        "channels": [
            {"name": "node-zero-entrance", "type": "text",
             "topic": "Welcome to The Shadow Syndicate. You are now in Node Zero."},
            {"name": "syndicate-charter", "type": "text",
             "topic": "The immutable laws of the Syndicate. Breaking them voids your access."},
            {"name": "verify-terminal", "type": "text",
             "topic": "Establish your uplink here. Verification required for full access."},
        ],
        "admin_only_send": ["syndicate-charter", "node-zero-entrance"],
        "ghost_can_send": ["verify-terminal"],  # only this channel allows Ghost messages
    },
    # ── ANNOUNCEMENTS ──
    {
        "name": "INTEL DISPATCH",
        "everyone_view": False,
        "operative_send": False,  # announcements are read-only
        "channels": [
            {"name": "syndicate-broadcasts", "type": "text",
             "topic": "Major operational updates from the Syndicate."},
            {"name": "patch-notes", "type": "text",
             "topic": "Platform changelogs, game updates, contract upgrades."},
            {"name": "dark-pool-reports", "type": "text",
             "topic": "Treasury metrics, staking data, house performance."},
            {"name": "surveillance-feed", "type": "text",
             "topic": "Live feed from the surface world. Follow @TheShadowSynd on X."},
        ],
        "admin_only_send": ["syndicate-broadcasts", "patch-notes", "dark-pool-reports"],
    },
    # ── COMMUNITY ──
    {
        "name": "THE FLOOR",
        "everyone_view": False,
        "operative_send": True,
        "channels": [
            {"name": "the-lounge", "type": "text",
             "topic": "General comms. Keep it encrypted, keep it clean."},
            {"name": "tactical-chat", "type": "text",
             "topic": "Strategy, odds calculation, game theory. Sharpen your edge."},
            {"name": "memes-and-glitches", "type": "text",
             "topic": "Transmission artifacts. Low-effort, high-entropy."},
            {"name": "black-market", "type": "text",
             "topic": "Community marketplace. Trade at your own risk."},
        ],
    },
    # ── GAMES ──
    {
        "name": "GAME TABLES",
        "everyone_view": False,
        "operative_send": True,
        "channels": [
            {"name": "blind-mans-bluff", "type": "text",
             "topic": "Blackjack discussion. Hands, dealers, strategies."},
            {"name": "quantum-entropy", "type": "text",
             "topic": "Dice game. Probabilities, targets, multipliers."},
            {"name": "grid-breach", "type": "text",
             "topic": "Mines. Grid tactics, cash-out discipline."},
            {"name": "big-win-flex", "type": "text",
             "topic": "Screenshot your wins. Prove it happened."},
        ],
    },
    # ── VIP ──
    {
        "name": "THE BACK ROOM",
        "everyone_view": False,
        "operative_send": False,  # Operatives can't even see this
        "vip_only": True,  # Night Raider only
        "channels": [
            {"name": "syndicate-vip", "type": "text",
             "topic": "Night Raider holder lounge. Private. Secure."},
            {"name": "governance-forum", "type": "text",
             "topic": "DAO proposals, voting, treasury decisions."},
            {"name": "private-tables", "type": "text",
             "topic": "Coordinate private game sessions. High rollers only."},
        ],
    },
    # ── DEV ──
    {
        "name": "DEV LAB",
        "everyone_view": False,
        "operative_send": True,
        "channels": [
            {"name": "tech-specs", "type": "text",
             "topic": "Technical deep dives. ZK circuits, Compact language, protocol design."},
            {"name": "contract-audit", "type": "text",
             "topic": "Smart contract discussion. Midnight Network development."},
            {"name": "bug-reports", "type": "text",
             "topic": "Report platform bugs. Include steps to reproduce."},
            {"name": "github-feed", "type": "text",
             "topic": "Automated GitHub activity feed."},
        ],
    },
    # ── VOICE ──
    {
        "name": "VOICE CHANNELS",
        "everyone_view": False,
        "operative_send": False,  # N/A for voice
        "channels": [
            {"name": "The Hacker's Den", "type": "voice"},
            {"name": "Blackjack Table", "type": "voice"},
            {"name": "Dice Pit", "type": "voice"},
            {"name": "Grid Room", "type": "voice"},
            {"name": "Syndicate Council", "type": "voice",
             "admin_only": True},  # Council+ only
        ],
    },
    # ── LOGS ──
    {
        "name": "SURVEILLANCE LOGS",
        "everyone_view": False,
        "operative_send": False,
        "channels": [
            {"name": "ghost-log", "type": "text",
             "topic": "Join/leave audit trail. Every entry and exit is recorded."},
            {"name": "mod-log", "type": "text",
             "topic": "Moderation actions. Bans, kicks, mutes, warnings."},
        ],
        "admin_only": True,  # Council+ only
    },
]

# CUSTOM STICKER EMOJIS — looked up by name at runtime
STICKER_EMOJI_NAMES = [
    "sticker_ghost",
    "sticker_crest",
    "sticker_skull",
    "sticker_dice",
    "sticker_chips",
    "sticker_cards",
    "sticker_martini",
    "sticker_shade_coin",
]

def get_sticker(guild, name):
    """Resolve a sticker emoji by name from the guild."""
    emoji = discord.utils.get(guild.emojis, name=name)
    return str(emoji) if emoji else f":{name}:"

STICKER_GHOST = "sticker_ghost"
STICKER_CREST = "sticker_crest"
STICKER_SKULL = "sticker_skull"
STICKER_DICE = "sticker_dice"
STICKER_CHIPS = "sticker_chips"
STICKER_CARDS = "sticker_cards"
STICKER_MARTINI = "sticker_martini"
STICKER_COIN = "sticker_shade_coin"
COIN_EMOJI = "coin_emoji"

# ──────────────────────────────────────────────
# RULES TEXT
# ──────────────────────────────────────────────

RULES = [
    {
        "title": "I. ZERO TRACE PROTOCOL",
        "body": "No doxxing. No sharing personal information — yours or anyone else's. "
                "Operatives remain encrypted. What happens in Node Zero stays in Node Zero.",
        "icon": STICKER_GHOST,
    },
    {
        "title": "II. ENCRYPTED CONDUCT",
        "body": "No hate speech, harassment, bigotry, or NSFW content outside designated areas. "
                "Treat fellow Operatives with the same discretion you expect.",
        "icon": STICKER_CREST,
    },
    {
        "title": "III. NO SIGNAL INTERFERENCE",
        "body": "No spam, flooding, excessive @mentions, or unsolicited DMs to members. "
                "Keep the channels clean. Don't degrade the signal-to-noise ratio.",
        "icon": STICKER_SKULL,
    },
    {
        "title": "IV. VERIFY YOUR HARDWARE",
        "body": "One identity per Operative. No alt accounts. No ban evasion. "
                "If you're caught running multiple personas, all will be terminated.",
        "icon": STICKER_DICE,
    },
    {
        "title": "V. RESPECT THE CHAIN",
        "body": "Follow Discord Terms of Service and Community Guidelines. "
                "The Syndicate operates on Discord's infrastructure — respect it.",
        "icon": STICKER_CHIPS,
    },
    {
        "title": "VI. OPERATIONAL SECURITY",
        "body": "No discussion of illegal activities. No market manipulation schemes. "
                "The Syndicate does not facilitate, endorse, or tolerate crime.",
        "icon": STICKER_CARDS,
    },
    {
        "title": "VII. CHANNEL DISCIPLINE",
        "body": "Keep content in its designated channel. Strategy goes in Tactical Chat. "
                "Memes go in Memes & Glitches. Bugs go in Bug Reports. No exceptions.",
        "icon": STICKER_MARTINI,
    },
    {
        "title": "VIII. THE ARCHITECT DECIDES",
        "body": "Staff rulings are final. If the Council or Architect makes a call, respect it. "
                "Appeals may be submitted via ticket — arguing in public channels will not be tolerated.",
        "icon": COIN_EMOJI,
    },
]

# ──────────────────────────────────────────────
# DATA PERSISTENCE
# ──────────────────────────────────────────────

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ──────────────────────────────────────────────
# PERSISTENT VIEWS
# ──────────────────────────────────────────────

class VerifyView(discord.ui.View):
    """Persistent view for the verification button in #verify-terminal."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Establish Uplink",
        style=discord.ButtonStyle.primary,
        custom_id="verify:establish_uplink",
        emoji="🔷",
    )
    async def establish_uplink(self, interaction: discord.Interaction, button: discord.ui.Button):
        """First button: show rules and ask for acceptance."""
        # Check if user is already verified
        guild = interaction.guild
        member = interaction.user
        ghost_role = discord.utils.get(guild.roles, name="Ghost")
        operative_role = discord.utils.get(guild.roles, name="Operative")

        if operative_role in member.roles:
            await interaction.response.send_message(
                "You are already verified, Operative. Your uplink is active.",
                ephemeral=True,
            )
            return

        # Build rules embed
        coin = get_sticker(interaction.guild, COIN_EMOJI)
        embed = discord.Embed(
            title=f"{coin} THE SYNDICATE CHARTER",
            description=(
                "By accepting, you agree to abide by all eight articles of the Charter. "
                "Violations result in immediate access revocation.\n\n"
                "Read carefully. There is no undo."
            ),
            color=discord.Color.from_rgb(192, 132, 252),
        )
        for rule in RULES:
            icon = get_sticker(interaction.guild, rule["icon"])
            embed.add_field(
                name=f"{icon} {rule['title']}",
                value=rule["body"],
                inline=False,
            )
        embed.set_footer(text="The Shadow Syndicate · Node Zero")

        view = AcceptCharterView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class AcceptCharterView(discord.ui.View):
    """Confirmation view for accepting the rules."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="I Accept the Charter",
        style=discord.ButtonStyle.success,
        custom_id="verify:accept_charter",
        emoji="✅",
    )
    async def accept_charter(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        ghost_role = discord.utils.get(guild.roles, name="Ghost")
        operative_role = discord.utils.get(guild.roles, name="Operative")

        if operative_role in member.roles:
            await interaction.response.send_message(
                "You're already verified, Operative.",
                ephemeral=True,
            )
            return

        # Promote: remove Ghost, add Operative
        try:
            if ghost_role in member.roles:
                await member.remove_roles(ghost_role, reason="Verification complete")
            await member.add_roles(operative_role, reason="Accepted the Syndicate Charter")

            await interaction.response.send_message(
                "⬡ Uplink established. Welcome to Node Zero, Operative.\n\n"
                "Your identity is now shielded. Your access is now unrestricted.\n"
                "Head to <#the-lounge> — the Syndicate awaits.",
                ephemeral=True,
            )

            # Send welcome in the-lounge
            lounge = discord.utils.get(guild.text_channels, name="the-lounge")
            if lounge:
                welcome_embed = discord.Embed(
                    title="⬡ New Operative Connected",
                    description=(
                        f"**{member.mention}** has established an uplink to Node Zero.\n"
                        f"The Syndicate grows stronger. Make them feel at home."
                    ),
                    color=discord.Color.from_rgb(45, 212, 191),
                )
                welcome_embed.set_thumbnail(url=member.display_avatar.url)
                welcome_embed.set_footer(text=f"Operative count: {len([m for m in guild.members if operative_role in m.roles])}")
                await lounge.send(embed=welcome_embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                "Error: Bot lacks permission to assign roles. Contact The Architect.",
                ephemeral=True,
            )
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred during verification. Please try again or open a ticket.\n```{e}```",
                ephemeral=True,
            )

    @discord.ui.button(
        label="Decline",
        style=discord.ButtonStyle.danger,
        custom_id="verify:decline",
        emoji="✖️",
    )
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Uplink declined. You remain a Ghost. If you change your mind, click **Establish Uplink** again.",
            ephemeral=True,
        )


# ──────────────────────────────────────────────
# BOT CLASS
# ──────────────────────────────────────────────

class NodeZero(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # needed for on_member_join and role checks
        intents.message_content = False
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        """Register persistent views and sync commands on startup."""
        self.add_view(VerifyView())
        self.add_view(AcceptCharterView())
        print("[NodeZero] Persistent views registered.")

        # Sync slash commands globally (for DMs) + per-guild (instant server availability)
        try:
            # Global sync first
            synced = await self.tree.sync()
            print(f"[NodeZero] Synced {len(synced)} commands globally: {[c.name for c in synced]}")
        except Exception as e:
            print(f"[NodeZero] Global sync failed: {e}")

        # Also sync to each guild the bot is in for instant availability
        for guild in self.guilds:
            try:
                await self.tree.sync(guild=guild)
                print(f"[NodeZero] Synced commands to guild: {guild.name}")
            except Exception as e:
                print(f"[NodeZero] Guild sync failed for {guild.name}: {e}")

    async def on_ready(self):
        print(f"[NodeZero] Connected as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Encrypted. Shielded. Watching.",
            )
        )

    async def on_member_join(self, member: discord.Member):
        """Auto-assign Ghost role to new members."""
        ghost_role = discord.utils.get(member.guild.roles, name="Ghost")
        if ghost_role is None:
            print(f"[WARNING] Ghost role not found in {member.guild.name}. Run /setup first.")
            return

        try:
            await member.add_roles(ghost_role, reason="New member — restricted to welcome channels")
            print(f"[NodeZero] Assigned Ghost to {member}")

            # Log to ghost-log
            ghost_log = discord.utils.get(member.guild.text_channels, name="ghost-log")
            if ghost_log:
                embed = discord.Embed(
                    title="⬡ New Ghost Detected",
                    description=f"{member.mention} (`{member.id}`) has entered Node Zero.",
                    color=discord.Color.dark_grey(),
                )
                embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, "R"))
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Ghost count: {len([m for m in member.guild.members if ghost_role in m.roles])}")
                await ghost_log.send(embed=embed)

        except discord.Forbidden:
            print(f"[ERROR] Cannot assign Ghost role to {member} — insufficient permissions.")

    async def on_member_remove(self, member: discord.Member):
        """Log member leaves."""
        ghost_log = discord.utils.get(member.guild.text_channels, name="ghost-log")
        if ghost_log:
            ghost_role = discord.utils.get(member.guild.roles, name="Ghost")
            operative_role = discord.utils.get(member.guild.roles, name="Operative")

            # Determine what they were
            was = "Ghost"
            if operative_role and operative_role in member.roles:
                was = "Operative"

            embed = discord.Embed(
                title="⬡ Connection Severed",
                description=f"{member.mention} (`{member.id}`) has left Node Zero.",
                color=discord.Color.red(),
            )
            embed.add_field(name="Status at Departure", value=was)
            embed.set_footer(text=f"Member since {member.joined_at.strftime('%Y-%m-%d') if member.joined_at else 'unknown'}")
            await ghost_log.send(embed=embed)


# ──────────────────────────────────────────────
# SLASH COMMANDS
# ──────────────────────────────────────────────

bot = NodeZero()


@bot.tree.command(name="setup", description="[Architect] Scaffold the entire Shadow Syndicate server structure.")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    """One-command server setup. Creates all roles, channels, permissions, and verification."""
    guild = interaction.guild

    if not guild:
        await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    current_channel = interaction.channel
    bot_member = guild.get_member(bot.user.id)

    try:
        # ── PHASE 0: Purge existing server structure ──
        purge_status = []

        # Delete all channels except this one
        for channel in guild.channels:
            if channel.id == current_channel.id:
                continue
            try:
                await channel.delete(reason="Shadow Syndicate server reset")
                purge_status.append(f"🗑️ #{channel.name}")
            except discord.Forbidden:
                purge_status.append(f"⚠️ No permission to delete #{channel.name}")
            except Exception as e:
                purge_status.append(f"⚠️ #{channel.name}: {e}")

        # Delete all roles except @everyone, bot-managed, and roles above the bot
        for role in sorted(guild.roles, key=lambda r: r.position, reverse=True):
            if role.name == "@everyone":
                continue
            if role.managed:
                purge_status.append(f"⏭️ @{role.name} (managed, skipped)")
                continue
            if bot_member and role >= bot_member.top_role:
                purge_status.append(f"⚠️ @{role.name} (above bot, skipped)")
                continue
            try:
                await role.delete(reason="Shadow Syndicate server reset")
                purge_status.append(f"🗑️ @{role.name}")
            except discord.Forbidden:
                purge_status.append(f"⚠️ No permission to delete @{role.name}")
            except Exception as e:
                purge_status.append(f"⚠️ @{role.name}: {e}")

        await interaction.followup.send(
            f"**Phase 0/5: Purge**\n" + "\n".join(purge_status[:25])
            + (f"\n... +{len(purge_status) - 25} more" if len(purge_status) > 25 else ""),
            ephemeral=True,
        )

        # ── PHASE 1: Create roles ──
        created_roles = {}
        existing_roles = {r.name: r for r in guild.roles}

        role_status = []

        for role_def in ROLES:
            name = role_def["name"]
            if name in existing_roles:
                created_roles[name] = existing_roles[name]
                role_status.append(f"⏭️ {name} — exists")
            else:
                new_role = await guild.create_role(
                    name=name,
                    color=role_def["color"],
                    hoist=role_def["hoist"],
                    mentionable=role_def["mentionable"],
                    permissions=role_def["permissions"],
                    reason="Shadow Syndicate setup",
                )
                created_roles[name] = new_role
                role_status.append(f"✅ {name} — created")

        # Reorder roles: highest role at the top of the list
        # The Architect at top, Ghost at bottom
        role_hierarchy = [r["name"] for r in ROLES]  # already ordered low→high
        role_hierarchy.reverse()  # now high→low as Discord expects
        position_roles = [created_roles[name] for name in role_hierarchy]
        # We need to position these relative to the bot's own role
        # Move the bot's role to the top first, then position others
        try:
            bot_member = guild.get_member(bot.user.id)
            if bot_member and bot_member.top_role:
                # Start from position 1 (below @everyone)
                for i, role in enumerate(position_roles):
                    # Position starts from bottom: higher number = lower on list
                    pos = len(position_roles) - i
                    if role.position != pos:
                        await role.edit(position=pos)
        except Exception as e:
            role_status.append(f"⚠️ Role reordering error: {e}")

        await interaction.followup.send(
            f"**Phase 1/5: Roles**\n" + "\n".join(role_status),
            ephemeral=True,
        )

        # ── PHASE 2: Create categories and channels ──
        existing_categories = {c.name: c for c in guild.categories}
        channel_status = []

        # Helper to get roles
        def get_role(name):
            return created_roles.get(name)

        ghost_role = get_role("Ghost")
        operative_role = get_role("Operative")
        night_raider_role = get_role("Night Raider")
        dark_pool_role = get_role("Dark Pool Staker")
        council_role = get_role("Syndicate Council")
        architect_role = get_role("The Architect")
        operator_role = get_role("Operator")

        admin_roles = [architect_role, council_role, operator_role]

        for cat_def in CATEGORIES:
            cat_name = cat_def["name"]

            # Create or get category
            if cat_name in existing_categories:
                category = existing_categories[cat_name]
                channel_status.append(f"⏭️ Category: {cat_name} — exists")
            else:
                # Build permission overwrites for the category
                overwrites = {}

                if cat_def.get("everyone_view", False):
                    # Welcome category: everyone can see
                    overwrites[guild.default_role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,  # Ghosts need to send in verify-terminal; we'll restrict per-channel
                        read_message_history=True,
                        connect=False,
                    )
                else:
                    # All other categories: deny everyone
                    overwrites[guild.default_role] = discord.PermissionOverwrite(
                        view_channel=False,
                        send_messages=False,
                        connect=False,
                    )

                # Operative access
                if not cat_def.get("vip_only", False) and not cat_def.get("admin_only", False):
                    if operative_role:
                        overwrites[operative_role] = discord.PermissionOverwrite(
                            view_channel=True,
                            send_messages=True if cat_def.get("operative_send", True) else False,
                            read_message_history=True,
                            connect=True if any(ch["type"] == "voice" for ch in cat_def["channels"]) else None,
                            speak=True if any(ch["type"] == "voice" for ch in cat_def["channels"]) else None,
                        )

                # Night Raider VIP access
                if cat_def.get("vip_only", False):
                    if night_raider_role:
                        overwrites[night_raider_role] = discord.PermissionOverwrite(
                            view_channel=True,
                            send_messages=True,
                            read_message_history=True,
                        )

                # Admin access
                if cat_def.get("admin_only", False) or any(c.get("admin_only") for c in cat_def["channels"]):
                    for admin_role in admin_roles:
                        if admin_role:
                            overwrites[admin_role] = discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                read_message_history=True,
                                connect=True,
                                speak=True,
                            )

                # Always let admins see
                for admin_role in admin_roles:
                    if admin_role and admin_role not in overwrites:
                        overwrites[admin_role] = discord.PermissionOverwrite(
                            view_channel=True,
                            send_messages=True,
                            read_message_history=True,
                            connect=True,
                            speak=True,
                        )

                category = await guild.create_category(
                    name=cat_name,
                    overwrites=overwrites,
                    reason="Shadow Syndicate setup",
                )
                channel_status.append(f"✅ Category: {cat_name} — created")

            # ── Create channels inside category ──
            existing_channels = {c.name: c for c in category.channels}

            for ch_def in cat_def["channels"]:
                ch_name = ch_def["name"]

                if ch_name in existing_channels:
                    channel_status.append(f"   ⏭️ #{ch_name} — exists")
                    continue

                # Build channel-specific overwrites
                ch_overwrites = {}

                # If admin_only_send specified for this channel
                if ch_name in cat_def.get("admin_only_send", []):
                    # Deny send for @everyone (Ghosts inherit this)
                    # This is critical: prevents unverified users from posting in rules/announcements
                    ch_overwrites[guild.default_role] = discord.PermissionOverwrite(
                        send_messages=False,
                    )
                    # Deny send for Operatives but allow view
                    if operative_role:
                        ch_overwrites[operative_role] = discord.PermissionOverwrite(
                            send_messages=False,
                        )
                    # Allow send for admins
                    for admin_role in admin_roles:
                        if admin_role:
                            ch_overwrites[admin_role] = discord.PermissionOverwrite(
                                send_messages=True,
                            )

                # If channel is admin-only
                if ch_def.get("admin_only", False):
                    # Override everyone to deny
                    ch_overwrites[guild.default_role] = discord.PermissionOverwrite(
                        view_channel=False,
                        connect=False,
                    )
                    if operative_role:
                        ch_overwrites[operative_role] = discord.PermissionOverwrite(
                            view_channel=False,
                            connect=False,
                        )
                    for admin_role in admin_roles:
                        if admin_role:
                            ch_overwrites[admin_role] = discord.PermissionOverwrite(
                                view_channel=True,
                                connect=True,
                                speak=True,
                            )

                # For ghost_can_send channels: explicitly allow @everyone to send
                # This is the only place Ghosts should be able to type
                if ch_name in cat_def.get("ghost_can_send", []):
                    ch_overwrites[guild.default_role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                    )

                if ch_def["type"] == "text":
                    new_ch = await category.create_text_channel(
                        name=ch_name,
                        topic=ch_def.get("topic", ""),
                        overwrites=ch_overwrites,
                        reason="Shadow Syndicate setup",
                    )
                    channel_status.append(f"   ✅ #{ch_name} — created")

                elif ch_def["type"] == "voice":
                    new_ch = await category.create_voice_channel(
                        name=ch_name,
                        overwrites=ch_overwrites,
                        reason="Shadow Syndicate setup",
                    )
                    channel_status.append(f"   ✅ 🔊 {ch_name} — created")

        await interaction.followup.send(
            f"**Phase 2/5: Channels**\n" + "\n".join(channel_status[-30:])
            + ("\n... (truncated)" if len(channel_status) > 30 else ""),
            ephemeral=True,
        )

        # ── PHASE 3: Post rules embed ──
        rules_channel = discord.utils.get(guild.text_channels, name="syndicate-charter")
        if rules_channel:
            # Check for existing rules message
            existing_rules = False
            async for msg in rules_channel.history(limit=10):
                if msg.author == bot.user and msg.embeds:
                    existing_rules = True
                    break

            if not existing_rules:
                coin = get_sticker(guild, COIN_EMOJI)
                rules_embed = discord.Embed(
                    title=f"{coin} THE SYNDICATE CHARTER",
                    description=(
                        "**These are the immutable laws of The Shadow Syndicate.**\n"
                        "Violation of any article may result in immediate access revocation.\n"
                        "By verifying, you acknowledge and accept all terms below.\n\n"
                        "*Last amended: Phase 01 — Foundation*"
                    ),
                    color=discord.Color.from_rgb(192, 132, 252),
                )
                for rule in RULES:
                    icon = get_sticker(guild, rule["icon"])
                    rules_embed.add_field(
                        name=f"{icon} {rule['title']}",
                        value=rule["body"],
                        inline=False,
                    )
                rules_embed.set_footer(text="The Shadow Syndicate · Node Zero · Built on Midnight Network")

                # Attach rules banner
                banner_path = Path(__file__).parent / "assets" / "banners" / "rules_banner.png"
                if banner_path.exists():
                    rules_file = discord.File(str(banner_path), filename="rules_banner.png")
                    rules_embed.set_image(url="attachment://rules_banner.png")
                    await rules_channel.send(embed=rules_embed, file=rules_file)
                else:
                    await rules_channel.send(embed=rules_embed)

        await interaction.followup.send("**Phase 3/5: Rules** — Posted.", ephemeral=True)

        # ── PHASE 4: Post verification message ──
        verify_channel = discord.utils.get(guild.text_channels, name="verify-terminal")
        if verify_channel:
            existing_verify = False
            async for msg in verify_channel.history(limit=10):
                if msg.author == bot.user and msg.embeds:
                    existing_verify = True
                    break

            if not existing_verify:
                verify_embed = discord.Embed(
                    title="⬡ ESTABLISH UPLINK",
                    description=(
                        "Welcome to **Node Zero** — the encrypted heart of The Shadow Syndicate.\n\n"
                        "You are currently operating as a **Ghost** — your access is restricted.\n"
                        "To unlock full server access, you must accept the Syndicate Charter.\n\n"
                        "Click the button below to begin verification."
                    ),
                    color=discord.Color.from_rgb(45, 212, 191),
                )
                verify_embed.add_field(
                    name="What you'll get:",
                    value=(
                        "• Access to all game discussion channels\n"
                        "• Community chat with fellow Operatives\n"
                        "• Development updates and roadmap tracking\n"
                        "• Event participation and giveaways"
                    ),
                )
                verify_embed.add_field(
                    name="What we require:",
                    value=(
                        "• Acceptance of the 8-article Syndicate Charter\n"
                        "• Respect for fellow Operatives\n"
                        "• No disruption of channel operations"
                    ),
                )
                verify_embed.set_footer(text="The Shadow Syndicate · Phase 01 · Concept Demo")

                await verify_channel.send(embed=verify_embed, view=VerifyView())

        await interaction.followup.send("**Phase 4/5: Verification** — Posted.", ephemeral=True)

        # ── PHASE 5: Post welcome message ──
        welcome_channel = discord.utils.get(guild.text_channels, name="node-zero-entrance")
        if welcome_channel:
            existing_welcome = False
            async for msg in welcome_channel.history(limit=10):
                if msg.author == bot.user and msg.embeds:
                    existing_welcome = True
                    break

            if not existing_welcome:
                coin = get_sticker(guild, COIN_EMOJI)
                welcome_embed = discord.Embed(
                    title=f"{coin} NODE ZERO — YOU HAVE ARRIVED",
                    description=(
                        "**The Shadow Syndicate** is the first privacy-first gambling platform "
                        "built on the **Midnight Network**.\n\n"
                        "Zero-knowledge proofs protect your identity. "
                        "Provably fair games ensure the house cannot cheat. "
                        "Your bets are encrypted — only your wins hit the chain.\n\n"
                        "**Three games. Infinite privacy. One Syndicate.**\n"
                        "*Powered by $SHADE — the native token of the Syndicate.*"
                    ),
                    color=discord.Color.from_rgb(45, 212, 191),
                )
                welcome_embed.add_field(
                    name="🂡 Blind Man's Bluff",
                    value="Classic Blackjack. ZK-verified deck shuffling.",
                    inline=True,
                )
                welcome_embed.add_field(
                    name="🎲 Quantum Entropy",
                    value="Set your target. The mathematics decides.",
                    inline=True,
                )
                welcome_embed.add_field(
                    name="💣 Grid Breach",
                    value="Navigate the minefield. Cash out or crash out.",
                    inline=True,
                )
                welcome_embed.add_field(
                    name="🔗 Website",
                    value="[shadowsyndicate.xyz](https://shadowsyndicate.xyz)",
                    inline=True,
                )
                welcome_embed.add_field(
                    name="🐦 Twitter/X",
                    value="[@TheShadowSynd](https://x.com/TheShadowSynd)",
                    inline=True,
                )
                welcome_embed.add_field(
                    name="💬 Discord",
                    value="You're already here, Operative.",
                    inline=True,
                )
                welcome_embed.set_footer(text="Proceed to #verify-terminal to establish your uplink.")

                banner_path = Path(__file__).parent / "assets" / "banners" / "welcome_banner.png"
                if banner_path.exists():
                    welcome_file = discord.File(str(banner_path), filename="welcome_banner.png")
                    welcome_embed.set_image(url="attachment://welcome_banner.png")
                    await welcome_channel.send(embed=welcome_embed, file=welcome_file)
                else:
                    await welcome_channel.send(embed=welcome_embed)

        await interaction.followup.send("**Phase 5/5: Welcome** — Posted.", ephemeral=True)

        # ── FINAL ──
        final_embed = discord.Embed(
            title="✅ Node Zero is Online",
            description=(
                "The Shadow Syndicate server has been fully scaffolded.\n\n"
                "**Next steps:**\n"
                "1. Verify the bot's role is at the top of the role hierarchy\n"
                "2. Test verification: join as a new account or have someone verify\n"
                "3. Customize the welcome/rules embeds if desired\n"
                "4. Create invite links through Discord\n\n"
                "Run `/setup` again to re-create any missing elements (existing items are skipped)."
            ),
            color=discord.Color.green(),
        )
        await interaction.followup.send(embed=final_embed, ephemeral=True)

    except discord.Forbidden as e:
        await interaction.followup.send(
            f"**Permission Error:** The bot lacks required permissions.\n"
            f"```{e}```\n"
            f"Ensure the bot has Administrator permission or at minimum: "
            f"Manage Roles, Manage Channels, Manage Webhooks, Send Messages, Embed Links.",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.followup.send(
            f"**Setup Error:**\n```{e}```\n"
            f"The setup may be partially complete. Running `/setup` again will skip existing items.",
            ephemeral=True,
        )
        raise


@bot.tree.command(name="verify", description="Begin the verification process to become an Operative.")
async def verify(interaction: discord.Interaction):
    """Manual verification trigger."""
    operative_role = discord.utils.get(interaction.guild.roles, name="Operative")
    if operative_role and operative_role in interaction.user.roles:
        await interaction.response.send_message(
            "You are already verified, Operative.",
            ephemeral=True,
        )
        return

    # Show rules and acceptance
    coin = get_sticker(interaction.guild, COIN_EMOJI)
    embed = discord.Embed(
        title=f"{coin} THE SYNDICATE CHARTER",
        description=(
            "By accepting, you agree to abide by all eight articles. "
            "Read carefully. There is no undo."
        ),
        color=discord.Color.from_rgb(192, 132, 252),
    )
    for rule in RULES:
        icon = get_sticker(interaction.guild, rule["icon"])
        embed.add_field(
            name=f"{icon} {rule['title']}",
            value=rule["body"],
            inline=False,
        )
    embed.set_footer(text="The Shadow Syndicate · Node Zero")

    view = AcceptCharterView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="rules", description="View the Syndicate Charter.")
async def rules_cmd(interaction: discord.Interaction):
    """Display rules."""
    coin = get_sticker(interaction.guild, COIN_EMOJI)
    embed = discord.Embed(
        title=f"{coin} THE SYNDICATE CHARTER",
        description="The immutable laws of The Shadow Syndicate.",
        color=discord.Color.from_rgb(192, 132, 252),
    )
    for rule in RULES:
        icon = get_sticker(interaction.guild, rule["icon"])
        embed.add_field(
            name=f"{icon} {rule['title']}",
            value=rule["body"],
            inline=False,
        )
    embed.set_footer(text="The Shadow Syndicate · Node Zero")
    await interaction.response.send_message(embed=embed, ephemeral=False)


@bot.tree.command(name="ping", description="Check if NodeZero is online.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Uplink active. Latency: {round(bot.latency * 1000)}ms",
        ephemeral=True,
    )


@bot.tree.command(name="post-verify", description="[Admin] Re-post the verification message in this channel.")
@app_commands.default_permissions(manage_guild=True)
async def post_verify(interaction: discord.Interaction):
    """Re-post the verification button without purging the server."""
    embed = discord.Embed(
        title="⬡ NODE ZERO VERIFICATION",
        description="Welcome to the Shadow Syndicate. Click below to verify and gain full server access.",
        color=discord.Color.from_rgb(45, 212, 191),
    )
    embed.add_field(name="Step 1", value="Click **Establish Uplink** below.", inline=False)
    embed.add_field(name="Step 2", value="Read and accept the Syndicate Charter.", inline=False)
    embed.add_field(name="Step 3", value="You'll be promoted to Operative — full access granted.", inline=False)
    embed.set_footer(text="The Shadow Syndicate · Node Zero")
    await interaction.channel.send(embed=embed, view=VerifyView())
    await interaction.response.send_message("✅ Verification message posted in this channel.", ephemeral=True)


@bot.tree.command(name="status", description="[Council] Set the bot's status.")
@app_commands.default_permissions(administrator=True)
async def set_status(interaction: discord.Interaction, text: str):
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=text)
    )
    await interaction.response.send_message(f"Status updated: Watching \"{text}\"", ephemeral=True)


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Use python-dotenv if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not set.")
        print("Create a .env file with: DISCORD_TOKEN=your_bot_token_here")
        print("Or set the environment variable directly.")
        sys.exit(1)

    bot.run(TOKEN)
