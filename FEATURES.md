# League of Legends Discord Bot - Feature Summary

## Overview
A comprehensive Discord bot for managing League of Legends custom games with 10 players. The bot helps balance teams, track player performance, and manage game sessions.

---

## Core Features

### 1. Account Management

#### `/connect` - Link League Account
- **Description**: Connect your Discord account to your League of Legends Riot account
- **Parameters**:
  - `game_name`: Your League username
  - `tag_line`: Your Riot tag (e.g., NA1, EUW) - no hashtag needed
- **Features**:
  - Validates Riot account exists
  - Fetches highest achieved rank/tier from Riot API
  - Stores account information in Supabase database
  - Prevents duplicate connections (one League account per Discord user)
  - Initializes custom MMR at 1000
- **Response**: Shows connected account, current tier, and custom MMR

#### `/me` - View Your Profile
- **Description**: View your connected League account information
- **Features**:
  - Displays Riot ID (username#tag)
  - Shows ranked tier and rank
  - Shows current custom MMR
- **Response**: Profile embed with account details

---

### 2. Team Generation

#### `/generate-teams` - Manual Team Selection
- **Description**: Generate balanced teams from 10 manually selected Discord users
- **Parameters**: 10 required player mentions (player1 through player10)
- **Features**:
  - Validates all 10 players have connected accounts
  - Ensures all players are unique
  - Uses custom MMR for team balancing
  - Generates match ID for result tracking
- **Algorithm**:
  - Evaluates all 252 possible team combinations (C(10,5))
  - Selects from top 20 most balanced combinations
  - Randomly picks one for variety
  - Minimizes MMR difference between teams
- **Response**: 
  - Two balanced teams with player mentions
  - Total MMR for each team
  - MMR difference between teams
  - Interactive buttons to record match results

#### `/generate-teams-voice` - Voice Channel Auto-Detection
- **Description**: Generate balanced teams from players in your current voice channel
- **Features**:
  - Automatically detects all members in your voice channel
  - Excludes bots
  - Requires exactly 10 players
  - Same balancing algorithm as manual selection
- **Response**: Same as `/generate-teams` with voice channel context

---

### 3. Match Result Recording

#### Interactive Match Result Buttons
- **Description**: Record match outcomes directly from team generation message
- **Features**:
  - **Team 1 Won** button: Records Team 1 victory
  - **Team 2 Won** button: Records Team 2 victory
  - **Cancel** button: Cancels result recording
  - Buttons disable after result is recorded
  - Shows MMR changes for all players
- **MMR System**:
  - Uses Elo-based calculation
  - Winning team gains MMR, losing team loses MMR
  - Amount based on team average MMR difference
  - All players on same team get same change
- **Response**: 
  - Confirmation message
  - Individual MMR changes for all 10 players
  - Match stored in database for history

---

### 4. Player Attendance

#### `/attendance-check` (Attendance Check)
- **Description**: Check who's ready to play today
- **Features**:
  - Interactive buttons for players to mark themselves as ready
  - Real-time player list updates
  - Shows count of ready players (target: 10)
  - **"I'm Ready!"** button: Add yourself to the list
  - **"Can't Play"** button: Remove yourself from the list
  - **"Clear List"** button: Moderators can clear the entire list
  - Persistent view (doesn't expire)
- **Use Case**: Quick way to see who's available for custom games

---

### 5. MMR History & Statistics

#### `/mmr-history` - MMR Progression Graph
- **Description**: View your MMR progression over time with visual graph
- **Features**:
  - Generates matplotlib graph showing MMR over matches
  - Green markers for wins, red markers for losses
  - Shows current MMR
  - Dark theme optimized for Discord
  - Displays match-by-match progression
- **Response**: 
  - PNG image graph embedded in Discord
  - Shows all matches played
  - Win/loss indicators on each match point

#### `/leaderboard` - MMR Rankings
- **Description**: View top players by custom MMR
- **Parameters**:
  - `limit`: Number of players to show (default: 20, max: 50)
- **Features**:
  - Shows top players ranked by custom MMR
  - Displays player mentions, Riot ID, MMR, and ranked tier
  - Medal emojis for top 3 (🥇🥈🥉)
  - Shows your rank if you're on the leaderboard
  - Shows estimated rank if you're not in top N
- **Response**: 
  - Ranked list embed
  - Your personal rank information

---

## Technical Features

### Backend Architecture
- **FastAPI REST API**: Handles all business logic
- **Supabase Database**: Stores user accounts, matches, and MMR data
- **Riot Games API Integration**: Fetches player ranks and account info
- **Async/Await**: Fully asynchronous for performance

### Data Storage
- **User Accounts**: Discord ID, Riot username/tag, PUUID, highest tier/rank
- **Custom MMR**: Separate MMR system for custom games (starts at 1000)
- **Match History**: All matches recorded with:
  - Team compositions
  - Match results
  - MMR changes
  - Timestamps
  - Pre-match MMR values

### Team Balancing Algorithm
- **Method**: Exhaustive search of all combinations
- **Optimization**: Selects from top 20 most balanced teams
- **Randomization**: Random selection from top candidates for variety
- **Metric**: Minimizes absolute MMR difference between teams

### MMR Calculation
- **System**: Elo-based rating system
- **Formula**: Based on team average MMR difference
- **K-Factor**: Adjustable based on match outcome
- **Fairness**: All players on same team get identical MMR change

---

## Command Summary

| Command | Description | Parameters |
|---------|-------------|------------|
| `/connect` | Link League account | `game_name`, `tag_line` |
| `/me` | View your profile | None |
| `/generate-teams` | Generate teams (manual) | 10 player mentions |
| `/generate-teams-voice` | Generate teams (voice) | None |
| `/attendance-check` | Player attendance check | None |
| `/mmr-history` | View MMR graph | None |
| `/leaderboard` | View rankings | `limit` (optional) |

---

## Deployment Features

### 24/7 Hosting Support
- **Render**: Free tier with spin-down prevention
- **Railway**: Always-on hosting ($5/month credit)
- **Vultr**: VPS option ($2.50-6/month)
- **Docker-ready**: Can be containerized
- **Environment-based config**: All secrets in environment variables

### Startup Scripts
- **start.py**: Python script to run both FastAPI and Discord bot
- **start.sh**: Shell wrapper for compatibility
- **Process management**: Handles both services gracefully

---

## Future Enhancement Ideas

- [ ] Queue system for matchmaking
- [ ] Role preferences for team generation
- [ ] Statistics dashboard
- [ ] Match replay/analysis
- [ ] Seasonal MMR resets
- [ ] Team captain selection
- [ ] Automated match scheduling
- [ ] Integration with League client API

---

## Data Privacy & Security

- **One Account Per User**: Each League account can only be connected to one Discord account
- **No Sensitive Data**: Only stores public Riot account information
- **Secure API Keys**: All keys stored in environment variables
- **Rate Limiting**: Respects Riot API rate limits

---

## Supported Regions

All Riot Games API regions are supported:
- North America (NA1)
- Europe West (EUW1)
- Europe Nordic & East (EUN1)
- Korea (KR)
- Brazil (BR1)
- And all other Riot regions

