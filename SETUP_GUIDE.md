# Discord Bot Setup & Testing Guide

## Step 1: Enable Bot Intents

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your bot application
3. Go to **Bot** section
4. Under **Privileged Gateway Intents**, enable:
   - ✅ **Server Members Intent**
   - ✅ **Message Content Intent** (if available)

## Step 2: Generate Bot Invite Link

1. In Discord Developer Portal, go to **OAuth2** → **URL Generator**
2. Select **Scopes**:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select **Bot Permissions**:
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Use Slash Commands
4. Copy the generated URL at the bottom
5. Open the URL in your browser and invite the bot to your server

## Step 3: Start the FastAPI Backend

The bot needs the API backend to be running. Open a terminal and run:

```bash
uvicorn api.main:app --reload
```

Or if you prefer to run it directly:

```bash
python -m api.main
```

The API will start on `http://0.0.0.0:8000` (or your configured port).

## Step 4: Start the Discord Bot

Open a **new terminal window** and run:

```bash
python bot/main.py
```

You should see:
- `Logged in as [YourBotName] (ID: [bot_id])`
- `Bot is ready! Connected to X guild(s)`
- `Synced X command(s)`

## Step 5: Test the Bot

1. Go to your Discord server where you invited the bot
2. Type `/` in a channel - you should see:
   - `/connect` - Connect your League of Legends account
   - `/generate-teams` - Generate balanced teams

### Test `/connect` command:
```
/connect game_name:YourGameName tag_line:YourTagLine
```

Example:
```
/connect game_name:SummonerName tag_line:NA1
```

### Test `/generate-teams` command:
```
/generate-teams player1:@User1 player2:@User2 ... player10:@User10
```

## Troubleshooting

### Bot doesn't respond to commands
- Make sure the FastAPI backend is running
- Check that the bot is online in your server
- Wait a few minutes after inviting - commands may take time to sync globally
- Try restarting the bot

### "Invalid Discord bot token" error
- Check your `.env` file has `DISCORD_BOT_TOKEN` set correctly
- Make sure there are no extra spaces or quotes in the token

### "Configuration error" when starting
- Verify all required environment variables are in your `.env` file:
  - `DISCORD_BOT_TOKEN`
  - `RIOT_API_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`

### Commands not appearing
- Make sure you enabled `applications.commands` scope in the invite URL
- Commands can take up to 1 hour to sync globally (usually instant though)
- Try restarting the bot to force a sync

### API connection errors
- Make sure the FastAPI backend is running on the correct port (default: 8000)
- Check that `API_HOST` and `API_PORT` in `.env` match your setup

## Quick Test Script

You can also test the API directly:

```bash
# Test API health
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

