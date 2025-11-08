# Discord League Team Generator Bot

A Discord bot that helps generate balanced teams for League of Legends custom games by connecting user Discord accounts to their League of Legends accounts. The bot uses ranked solo queue data to automatically calculate initial MMR and provides an Elo-based rating system for tracking player performance.

## Features

### Account Management
- **`/connect`** - Link your Discord account to your League of Legends Riot account
  - Automatically fetches your ranked solo queue tier and rank
  - Calculates initial MMR based on your tier (if MMR doesn't exist)
  - Master = 800 MMR, Grandmaster = 900 MMR, Challenger = 1000 MMR
  - Other tiers: Base tier value (100-700) + rank bonus (0-75)
- **`/me`** - View your connected account and current MMR

### Team Generation
- **`/generate-teams`** - Generate balanced teams from 10 manually selected players
- **`/generate-teams-voice`** - Automatically generate teams from players in your voice channel
- **Balancing Algorithm**:
  - Evaluates all 252 possible team combinations (C(10,5))
  - Selects from top 20 most balanced combinations
  - Randomly picks one for variety
  - Minimizes MMR difference between teams

### Match Tracking
- Interactive buttons to record match results
- Elo-based MMR system that updates after each match
- Match history stored in database

### Player Management
- **`/인원췤`** - Check who's ready to play (interactive attendance system)

### Statistics
- **`/mmr-history`** - View your MMR progression graph
- **`/leaderboard`** - View top players by MMR

## Setup

### Prerequisites
- Python 3.10+
- Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))
- Riot Games API Key (from [Riot Developer Portal](https://developer.riotgames.com/))
- Supabase account and project

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/league_helper_discord.git
cd league_helper_discord
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env` (if it exists) or create a `.env` file
   - Fill in your credentials:
     ```
     DISCORD_BOT_TOKEN=your_discord_bot_token
     RIOT_API_KEY=your_riot_api_key
     SUPABASE_URL=your_supabase_url
     SUPABASE_KEY=your_supabase_key
     DEFAULT_REGION=na1
     ```

4. **Set up Supabase database:**
   - Run the migrations in `supabase/migrations/` to create the necessary tables
   - Or use the Supabase MCP tool to set up the database

5. **Start the services:**
```bash
python3 start.py
```

This will start both the FastAPI backend and Discord bot together.

### Manual Start (Development)

For development, you can run services separately:

**Terminal 1 - FastAPI:**
```bash
uvicorn api.main:app --reload
```

**Terminal 2 - Discord Bot:**
```bash
python bot/main.py
```

## Usage

### Connecting Your Account
```
/connect game_name:YourUsername tag_line:NA1
```

The bot will:
1. Fetch your ranked solo queue tier and rank from Riot API
2. Calculate your initial MMR based on your tier (if you don't have one yet)
3. Store your account information

### Generating Teams

**Manual Selection:**
```
/generate-teams player1:@Player1 player2:@Player2 ... player10:@Player10
```

**Voice Channel Auto-Detection:**
```
/generate-teams-voice
```
(Use this command while in a voice channel with 10 players)

### Recording Match Results
After teams are generated, use the interactive buttons:
- **Team 1 Won** - Record Team 1 victory
- **Team 2 Won** - Record Team 2 victory
- **Cancel** - Cancel result recording

MMR will be automatically updated for all players based on the match result.

### Viewing Statistics
```
/mmr-history          # View your MMR progression graph
/leaderboard          # View top players by MMR
/leaderboard limit:50  # View top 50 players
```

## Architecture

### Components
- **Discord Bot** (`bot/`): Handles user interactions via slash commands
- **FastAPI Backend** (`api/`): REST API for Riot API integration and team generation
- **Supabase Database**: Stores user accounts, League connections, matches, and MMR data
- **Riot Games API**: Fetches player ranked solo queue tier and rank

### MMR System
- **Initial MMR**: Automatically calculated from ranked solo queue tier when connecting
  - Master: 800 MMR
  - Grandmaster: 900 MMR
  - Challenger: 1000 MMR
  - Other tiers: `(tier_value * 100) + (rank_bonus * 25)`
    - Tier values: Iron=1, Bronze=2, Silver=3, Gold=4, Platinum=5, Emerald=6, Diamond=7
    - Rank bonuses: I=75, II=50, III=25, IV=0
- **MMR Updates**: Elo-based system that adjusts after each match
- **Team Balancing**: Uses custom MMR to create balanced teams

### Team Balancing Algorithm
1. Evaluates all 252 possible team combinations (C(10,5))
2. Calculates MMR difference for each combination
3. Selects top 20 most balanced combinations
4. Randomly picks one from the top candidates for variety

## Deployment

### 24/7 Hosting Options

The bot can be deployed to run 24/7 on various platforms:

- **Render** (Free tier available, see `DEPLOYMENT.md` for spin-down prevention)
- **Railway** ($5/month credit)
- **Vultr** ($2.50-6/month VPS)
- **DigitalOcean** (Droplet)
- **Fly.io** (Free tier available)

See `DEPLOYMENT.md` for detailed deployment instructions.

### Environment Variables for Deployment
Make sure to set these in your hosting platform:
- `DISCORD_BOT_TOKEN`
- `RIOT_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `DEFAULT_REGION` (optional, default: na1)
- `PORT` (set by platform, default: 8000)
- `API_HOST` (optional, default: 0.0.0.0)
- `PYTHON_VERSION` (optional, default: 3.10)

## Command Reference

| Command | Description | Parameters |
|---------|-------------|------------|
| `/connect` | Link League account | `game_name`, `tag_line` |
| `/me` | View your profile | None |
| `/generate-teams` | Generate teams (manual) | 10 player mentions |
| `/generate-teams-voice` | Generate teams (voice) | None |
| `/인원췤` | Player attendance check | None |
| `/mmr-history` | View MMR graph | None |
| `/leaderboard` | View rankings | `limit` (optional) |

## Data Privacy & Security

- **One Account Per User**: Each League account can only be connected to one Discord account
- **No Sensitive Data**: Only stores public Riot account information
- **Secure API Keys**: All keys stored in environment variables
- **Rate Limiting**: Respects Riot API rate limits

## Supported Regions

All Riot Games API regions are supported:
- North America (NA1)
- Europe West (EUW1)
- Europe Nordic & East (EUN1)
- Korea (KR)
- Brazil (BR1)
- And all other Riot regions

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
