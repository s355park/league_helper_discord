"""Database service for Supabase operations."""
from supabase import create_client, Client
from typing import Optional, Dict, Any
from config import Config


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self):
        self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    async def get_or_create_user(self, discord_id: str, username: str) -> Dict[str, Any]:
        """Get or create a user in the database."""
        # Check if user exists
        result = self.client.table("users").select("*").eq("discord_id", discord_id).execute()
        
        if result.data:
            return result.data[0]
        
        # Create new user
        result = self.client.table("users").insert({
            "discord_id": discord_id,
            "username": username
        }).execute()
        
        return result.data[0] if result.data else {}
    
    async def get_league_account(self, discord_id: str, guild_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get League account for a Discord user with custom MMR for a specific guild."""
        result = self.client.table("league_accounts").select(
            "*"
        ).eq("discord_id", discord_id).execute()
        
        if not result.data:
            return None
        
        account = result.data[0]
        
        # Get MMR from guild_users if guild_id is provided
        if guild_id:
            guild_user = self.client.table("guild_users").select("custom_mmr").eq("guild_id", guild_id).eq("discord_id", discord_id).execute()
            if guild_user.data:
                account["custom_mmr"] = guild_user.data[0]["custom_mmr"]
            else:
                # Default MMR if user not in guild_users yet
                account["custom_mmr"] = 1000
        else:
            # Fallback to default if no guild_id
            account["custom_mmr"] = 1000
        
        return account
    
    async def upsert_league_account(
        self,
        discord_id: str,
        game_name: str,
        tag_line: str,
        puuid: Optional[str] = None,
        highest_tier: Optional[str] = None,
        highest_rank: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update a League account connection."""
        # Check if this PUUID is already connected to a different Discord account (only if PUUID is provided)
        if puuid:
            existing_puuid = self.client.table("league_accounts").select("discord_id").eq("puuid", puuid).execute()
            if existing_puuid.data:
                existing_discord_id = existing_puuid.data[0]["discord_id"]
                if existing_discord_id != discord_id:
                    raise ValueError(f"This League account is already connected to a different Discord user")
        
        # Check if this Discord account already has a League account
        existing_account = self.client.table("league_accounts").select("*").eq("discord_id", discord_id).execute()
        
        data = {
            "discord_id": discord_id,
            "game_name": game_name,
            "tag_line": tag_line,
            "puuid": puuid,
            "highest_tier": highest_tier,
            "highest_rank": highest_rank,
        }
        
        if existing_account.data:
            # Update existing account
            result = self.client.table("league_accounts").update(data).eq("discord_id", discord_id).execute()
        else:
            # Insert new account
            result = self.client.table("league_accounts").insert(data).execute()
        
        return result.data[0] if result.data else {}
    
    async def get_players_by_discord_ids(self, discord_ids: list[str], guild_id: Optional[str] = None) -> list[Dict[str, Any]]:
        """Get League account data for multiple Discord users with custom MMR for a specific guild."""
        result = self.client.table("league_accounts").select(
            "*"
        ).in_("discord_id", discord_ids).execute()
        
        players = []
        if not result.data:
            return players
        
        # Get MMRs from guild_users if guild_id is provided
        if guild_id:
            guild_users_result = self.client.table("guild_users").select("discord_id, custom_mmr").eq("guild_id", guild_id).in_("discord_id", discord_ids).execute()
            mmr_map = {gu["discord_id"]: gu["custom_mmr"] for gu in (guild_users_result.data if guild_users_result.data else [])}
        else:
            mmr_map = {}
        
        for account in result.data:
            discord_id = account["discord_id"]
            if guild_id and discord_id in mmr_map:
                account["custom_mmr"] = mmr_map[discord_id]
            else:
                # Default MMR if user not in guild_users yet
                account["custom_mmr"] = 1000
            players.append(account)
        
        return players
    
    async def get_or_create_guild_user(self, guild_id: str, discord_id: str, default_mmr: int = 1000) -> Dict[str, Any]:
        """Get or create a guild_user entry."""
        # Check if exists
        result = self.client.table("guild_users").select("*").eq("guild_id", guild_id).eq("discord_id", discord_id).execute()
        
        if result.data:
            return result.data[0]
        
        # Create new entry
        result = self.client.table("guild_users").insert({
            "guild_id": guild_id,
            "discord_id": discord_id,
            "custom_mmr": default_mmr
        }).execute()
        
        return result.data[0] if result.data else {}
    
    async def update_player_mmr(self, discord_id: str, new_mmr: int, guild_id: str) -> None:
        """Update a player's custom MMR for a specific guild."""
        # Ensure guild_user exists first
        await self.get_or_create_guild_user(guild_id, discord_id, new_mmr)
        
        # Update MMR
        self.client.table("guild_users").update({
            "custom_mmr": new_mmr,
            "updated_at": "now()"
        }).eq("guild_id", guild_id).eq("discord_id", discord_id).execute()
    
    async def record_match(
        self,
        match_id: str,
        team1_player_ids: list[str],
        team2_player_ids: list[str],
        winning_team: int,
        team1_avg_mmr: int,
        team2_avg_mmr: int,
        mmr_change: int,
        guild_id: str,
        player_mmrs: dict[str, int] = None
    ) -> None:
        """Record a match result in the database."""
        data = {
            "match_id": match_id,
            "team1_player_ids": team1_player_ids,
            "team2_player_ids": team2_player_ids,
            "winning_team": winning_team,
            "team1_avg_mmr": team1_avg_mmr,
            "team2_avg_mmr": team2_avg_mmr,
            "mmr_change": mmr_change,
            "guild_id": guild_id
        }
        
        if player_mmrs:
            data["player_mmrs"] = player_mmrs
        
        self.client.table("matches").insert(data).execute()
    
    async def get_match_by_id(self, match_id: str, guild_id: str) -> Optional[Dict[str, Any]]:
        """Get a match by match_id for a specific guild."""
        result = self.client.table("matches").select(
            "*"
        ).eq("match_id", match_id).eq("guild_id", guild_id).execute()
        
        if not result.data:
            return None
        
        return result.data[0]
    
    async def update_match_result(
        self,
        match_id: str,
        winning_team: int,
        team1_avg_mmr: int,
        team2_avg_mmr: int,
        mmr_change: int,
        guild_id: str
    ) -> None:
        """Update a match result in the database."""
        self.client.table("matches").update({
            "winning_team": winning_team,
            "team1_avg_mmr": team1_avg_mmr,
            "team2_avg_mmr": team2_avg_mmr,
            "mmr_change": mmr_change
        }).eq("match_id", match_id).eq("guild_id", guild_id).execute()
    
    async def get_subsequent_matches(
        self,
        after_timestamp: str,
        player_ids: list[str],
        guild_id: str
    ) -> list[Dict[str, Any]]:
        """Get all matches after a specific timestamp that involve any of the given players."""
        # Get all matches after the timestamp for this guild
        result = self.client.table("matches").select(
            "*"
        ).eq("guild_id", guild_id).gt("created_at", after_timestamp).order("created_at", desc=False).execute()
        
        if not result.data:
            return []
        
        # Filter to only matches involving any of the players
        subsequent_matches = []
        for match in result.data:
            team1_ids = match.get("team1_player_ids", [])
            team2_ids = match.get("team2_player_ids", [])
            all_match_ids = team1_ids + team2_ids
            
            # Check if any player from the corrected match is in this match
            if any(player_id in all_match_ids for player_id in player_ids):
                subsequent_matches.append(match)
        
        return subsequent_matches
    
    async def get_all_matches_for_guild(self, guild_id: str) -> list[Dict[str, Any]]:
        """Get all matches for a specific guild, ordered by creation time."""
        result = self.client.table("matches").select(
            "match_id, created_at, winning_team, team1_avg_mmr, team2_avg_mmr, team1_player_ids, team2_player_ids"
        ).eq("guild_id", guild_id).order("created_at", desc=False).execute()
        
        return result.data if result.data else []
    
    async def get_player_match_history(self, discord_id: str, guild_id: str, limit: int = 50) -> list[Dict[str, Any]]:
        """Get match history for a player with their MMR at match time in a specific guild."""
        # Get matches where player participated in this guild
        # First filter by guild_id, then check if player is in either team
        # We need to get all matches for this guild, then filter in Python for player participation
        result = self.client.table("matches").select(
            "id, match_id, created_at, winning_team, team1_player_ids, team2_player_ids, player_mmrs, mmr_change, guild_id"
        ).eq("guild_id", guild_id).order("created_at", desc=True).limit(limit * 2).execute()
        
        # Filter to only matches where this player participated
        player_matches = []
        for match in (result.data if result.data else []):
            team1_ids = match.get("team1_player_ids", [])
            team2_ids = match.get("team2_player_ids", [])
            if discord_id in team1_ids or discord_id in team2_ids:
                player_matches.append(match)
                if len(player_matches) >= limit:
                    break
        
        # Process the filtered matches
        matches = []
        for match in player_matches:
            # Determine which team the player was on
            team = 1 if discord_id in match.get("team1_player_ids", []) else 2
            won = match["winning_team"] == team
            
            # Get player's MMR at match time
            player_mmrs = match.get("player_mmrs", {})
            mmr_at_match = player_mmrs.get(discord_id) if isinstance(player_mmrs, dict) else None
            
            # Calculate MMR change for this player
            mmr_change = match.get("mmr_change", 0) if won else -match.get("mmr_change", 0)
            
            matches.append({
                "match_id": match.get("match_id"),
                "created_at": match.get("created_at"),
                "mmr_at_match": mmr_at_match,
                "mmr_change": mmr_change,
                "won": won
            })
        
        return matches
    
    async def get_mmr_leaderboard(self, guild_id: str, limit: int = 20) -> list[Dict[str, Any]]:
        """Get MMR leaderboard sorted by custom_mmr for a specific guild."""
        # Get guild_users with league accounts, ordered by MMR
        result = self.client.table("guild_users").select(
            "discord_id, custom_mmr, users(username, league_accounts(game_name, tag_line, highest_tier, highest_rank))"
        ).eq("guild_id", guild_id).order("custom_mmr", desc=True).limit(limit).execute()
        
        leaderboard = []
        for guild_user in (result.data if result.data else []):
            user_data = guild_user.get("users", {})
            if not user_data:
                continue
            
            # Skip users without league accounts
            league_accounts = user_data.get("league_accounts", [])
            if not league_accounts:
                continue
            
            # Get first league account (users should only have one)
            league_account = league_accounts[0] if isinstance(league_accounts, list) else league_accounts
            
            leaderboard.append({
                "discord_id": guild_user["discord_id"],
                "username": user_data.get("username", "Unknown"),
                "custom_mmr": guild_user.get("custom_mmr", 1000),
                "game_name": league_account.get("game_name") if isinstance(league_account, dict) else None,
                "tag_line": league_account.get("tag_line") if isinstance(league_account, dict) else None,
                "highest_tier": league_account.get("highest_tier") if isinstance(league_account, dict) else None,
                "highest_rank": league_account.get("highest_rank") if isinstance(league_account, dict) else None
            })
        
        return leaderboard

