# Discord League Team Generator Bot

A Discord bot that helps generate balanced teams for League of Legends custom games by connecting user Discord accounts to their League of Legends accounts and using their highest ever tier to create evenly matched teams.

## Features

- Connect Discord accounts to League of Legends accounts via Riot ID
- Fetch player tier data from Riot Games API
- Generate balanced teams for 10-player custom games
- Store user data in Supabase database

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your credentials:
- Discord Bot Token (from Discord Developer Portal)
- Riot Games API Key (from Riot Developer Portal)
- Supabase URL and Key

3. Run database migrations (Supabase will be set up via MCP)

4. Start the FastAPI backend:
```bash
uvicorn api.main:app --reload
```

5. Start the Discord bot:
```bash
python bot/main.py
```

## Usage

- `/connect <game_name> <tag_line>` - Link your League of Legends account
- `/generate-teams <@player1> <@player2> ... <@player10>` - Generate balanced teams from 10 players

## Architecture

- **Discord Bot**: Handles user interactions via slash commands
- **FastAPI Backend**: REST API for Riot API integration and team generation
- **Supabase**: Database for user accounts and League account connections
- **Riot Games API**: Fetches player tier and rank data

