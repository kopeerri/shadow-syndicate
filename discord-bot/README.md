# NodeZero — Shadow Syndicate Discord Bot

## Prerequisites

- Python 3.8+
- A Discord Application with a Bot token
- `discord.py` and `python-dotenv` installed

```bash
pip install -r requirements.txt
```

## Step 1: Create a Discord Bot

1. Go to https://discord.com/developers/applications
2. Click **New Application** → name it `NodeZero`
3. Go to **Bot** tab → **Add Bot**
4. Under **Privileged Gateway Intents**, enable:
   - **SERVER MEMBERS INTENT** (needed for auto-role on join)
5. Click **Reset Token** → copy the token

## Step 2: Invite the Bot

1. Go to **OAuth2** → **URL Generator**
2. Select scopes: `bot`, `applications.commands`
3. Bot permissions needed:
   - Manage Roles
   - Manage Channels
   - Send Messages
   - Embed Links
   - Read Message History
   - Add Reactions
   - Use External Emojis
   - Connect (for voice)
   - Speak (for voice)
   - Kick/Ban Members (for moderation commands)
   - Manage Messages (for moderation)
4. Open the generated URL and invite to your server

**CRITICAL:** After the bot joins, drag its role to the **top** of the role hierarchy
(below @everyone but above all other roles). Otherwise it cannot manage roles.

## Step 3: Configure

Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

Edit `.env` and paste your bot token:

```
DISCORD_TOKEN=your_actual_token_here
```

## Step 4: Run

```bash
python bot.py
```

You should see:
```
[NodeZero] Persistent views registered.
[NodeZero] Connected as NodeZero#XXXX (ID: ...)
```

## Step 5: Setup the Server

In Discord, run:

```
/setup
```

This will create everything in 5 phases:

| Phase | What it does |
|-------|-------------|
| 1/5   | Creates all 7 roles with proper hierarchy |
| 2/5   | Creates 8 categories and 28 channels with locked-down permissions |
| 3/5   | Posts the Syndicate Charter rules embed in #syndicate-charter |
| 4/5   | Posts the verification button in #verify-terminal |
| 5/5   | Posts the welcome embed in #node-zero-entrance |

Running `/setup` again is safe — it skips anything that already exists.

## Permission Model (How Ghosts Are Locked Out)

- **Ghost role** has `Permissions.none()` — zero inherited permissions
- **@everyone** is DENIED view on all categories except WELCOME & RULES
- Ghosts can ONLY see: `#node-zero-entrance`, `#syndicate-charter`, `#verify-terminal`
- Ghosts can ONLY type in: `#verify-terminal` (and only to click the button)
- All other 23 channels are invisible until verification
- After verification: Ghost removed, Operative added → full access

## Commands

| Command    | Who       | Purpose |
|-----------|-----------|---------|
| `/setup`   | Architect | Scaffold entire server |
| `/verify`  | Anyone    | Manual verification trigger |
| `/rules`   | Anyone    | Display the Syndicate Charter |
| `/ping`    | Anyone    | Check bot latency |
| `/status`  | Council   | Change bot status text |

## Testing Verification

To test that Ghosts are properly locked out:

1. Create an alt account or ask a friend to join
2. They should auto-receive the **Ghost** role
3. They should only see the WELCOME & RULES category
4. They should NOT be able to see any other channels
5. They should NOT be able to type in #syndicate-charter or #node-zero-entrance
6. They click **Establish Uplink** in #verify-terminal
7. They accept the charter
8. Ghost removed, Operative added → all channels unlock

## File Structure

```
discord-bot/
├── bot.py           # The entire bot (single file)
├── .env             # Your bot token (gitignored)
├── .env.example     # Token template
├── bot_data.json    # Persistent data (auto-created)
└── requirements.txt # Python dependencies
```
