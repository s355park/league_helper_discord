# Discord Bot Testing Guide

## Prerequisites

1. **FastAPI Backend** must be running:
   ```powershell
   python -m uvicorn api.main:app --reload
   ```
   You should see: `INFO: Uvicorn running on http://127.0.0.1:8000`

2. **Discord Bot** must be running:
   ```powershell
   python bot/main.py
   ```
   You should see:
   - `Logged in as [YourBotName]`
   - `Bot is ready! Connected to X guild(s)`
   - `Synced 2 command(s)`

3. **Bot must be invited** to your Discord server

## Testing Steps

### Step 1: Verify Commands Are Available

1. Go to your Discord server
2. Type `/` in any channel
3. You should see two commands:
   - `/connect` - Connect your League of Legends account
   - `/generate-teams` - Generate balanced teams

If commands don't appear:
- Wait 1-2 minutes (Discord can take time to sync globally)
- Make sure bot is online (green dot in member list)
- Restart the bot to force command sync

### Step 2: Test `/connect` Command

**Purpose**: Links your Discord account to your League of Legends account

**How to test**:
1. Type `/connect` in Discord
2. Fill in the parameters:
   - `game_name`: Your League username (e.g., "SummonerName")
   - `tag_line`: Your tag line (e.g., "NA1", "EUW", "KR1")

**Example**:
```
/connect game_name:MySummonerName tag_line:NA1
```

**Expected Results**:
- ✅ **Success**: You'll see an embed with:
  - "✅ Account Connected Successfully"
  - Your Riot ID (game_name#tag_line)
  - Your highest tier (e.g., "DIAMOND I", "GOLD IV", "Unranked")
- ❌ **Error**: You'll see an error message if:
  - Account not found (wrong Riot ID)
  - Riot API key invalid
  - API backend not running

**Test with a real Riot ID** you know exists to verify the connection works.

### Step 3: Test `/generate-teams` Command

**Purpose**: Creates balanced teams from 10 Discord users

**Prerequisites**: 
- At least 10 players need to have connected their accounts using `/connect`
- All 10 players must be in the same Discord server

**How to test**:
1. Type `/generate-teams` in Discord
2. Fill in all 10 player parameters by mentioning Discord users:
   - `player1`: @User1
   - `player2`: @User2
   - ... (up to player10)

**Example**:
```
/generate-teams player1:@Alice player2:@Bob player3:@Charlie player4:@David player5:@Eve player6:@Frank player7:@Grace player8:@Henry player9:@Ivy player10:@Jack
```

**Expected Results**:
- ✅ **Success**: You'll see an embed with:
  - Two balanced teams (Team 1 and Team 2)
  - Each player's name and tier
  - Total tier value for each team
  - Tier difference between teams (should be minimal)
- ❌ **Error**: You'll see an error if:
  - Not all 10 players have connected accounts
  - Duplicate players in the list
  - Less than 10 players provided
  - API backend not running

### Step 4: Test API Directly (Optional)

You can also test the FastAPI backend directly:

**Health Check**:
```powershell
curl http://localhost:8000/health
```
Should return: `{"status":"healthy"}`

**Root Endpoint**:
```powershell
curl http://localhost:8000/
```
Should return: `{"message":"Discord League Team Generator API","status":"running"}`

## Common Issues & Solutions

### Bot doesn't respond to commands
- ✅ Check FastAPI backend is running
- ✅ Check Discord bot is running (look for "Synced 2 command(s)")
- ✅ Wait 1-2 minutes for global command sync
- ✅ Restart the bot

### `/connect` returns "Account not found"
- ✅ Verify the Riot ID is correct (case-sensitive)
- ✅ Check the tag line format (e.g., "NA1" not "na1")
- ✅ Ensure the Riot API key is valid

### `/connect` returns "API configuration error"
- ✅ Check your `.env` file has `RIOT_API_KEY` set
- ✅ Verify the Riot API key is valid and not expired
- ✅ Check FastAPI backend is running

### `/generate-teams` returns "not connected"
- ✅ Make sure all 10 players have used `/connect` first
- ✅ Verify the players exist in the database (check Supabase)

### Commands don't appear in Discord
- ✅ Make sure you selected `applications.commands` scope when inviting
- ✅ Bot needs to sync commands (wait 1-2 minutes after start)
- ✅ Try restarting the bot

## Testing Checklist

- [ ] FastAPI backend running on port 8000
- [ ] Discord bot running and shows "Synced 2 command(s)"
- [ ] Bot is online in Discord (green dot)
- [ ] `/connect` command appears when typing `/`
- [ ] `/generate-teams` command appears when typing `/`
- [ ] `/connect` successfully links a League account
- [ ] `/generate-teams` successfully creates balanced teams (with 10 connected players)

## Quick Test Flow

1. **Start services**:
   - Terminal 1: `python -m uvicorn api.main:app --reload`
   - Terminal 2: `python bot/main.py`

2. **In Discord**:
   - Type `/connect` and link your account
   - Get 9 other people to do the same
   - Type `/generate-teams` with all 10 players

3. **Verify**:
   - Teams are balanced (low tier difference)
   - All players show their tiers
   - No errors in terminals

