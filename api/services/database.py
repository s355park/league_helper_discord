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
    
    async def get_league_account(self, discord_id: str) -> Optional[Dict[str, Any]]:
        """Get League account for a Discord user with custom MMR."""
        result = self.client.table("league_accounts").select(
            "*, users!inner(custom_mmr)"
        ).eq("discord_id", discord_id).execute()
        
        if not result.data:
            return None
        
        # Flatten the nested users data
        account = result.data[0]
        if "users" in account and account["users"]:
            account["custom_mmr"] = account["users"]["custom_mmr"]
            del account["users"]
        
        return account
    
    async def upsert_league_account(
        self,
        discord_id: str,
        game_name: str,
        tag_line: str,
        puuid: str,
        highest_tier: Optional[str] = None,
        highest_rank: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update a League account connection."""
        # Check if this PUUID is already connected to a different Discord account
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
    
    async def get_players_by_discord_ids(self, discord_ids: list[str]) -> list[Dict[str, Any]]:
        """Get League account data for multiple Discord users with custom MMR."""
        result = self.client.table("league_accounts").select(
            "*, users!inner(custom_mmr)"
        ).in_("discord_id", discord_ids).execute()
        
        # Flatten the nested users data
        players = []
        for account in (result.data if result.data else []):
            if "users" in account and account["users"]:
                account["custom_mmr"] = account["users"]["custom_mmr"]
                del account["users"]
            players.append(account)
        
        return players
    
    async def update_player_mmr(self, discord_id: str, new_mmr: int) -> None:
        """Update a player's custom MMR."""
        self.client.table("users").update({
            "custom_mmr": new_mmr
        }).eq("discord_id", discord_id).execute()
    
    async def record_match(
        self,
        match_id: str,
        team1_player_ids: list[str],
        team2_player_ids: list[str],
        winning_team: int,
        team1_avg_mmr: int,
        team2_avg_mmr: int,
        mmr_change: int,
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
            "mmr_change": mmr_change
        }
        
        if player_mmrs:
            data["player_mmrs"] = player_mmrs
        
        self.client.table("matches").insert(data).execute()
    
    async def get_player_match_history(self, discord_id: str, limit: int = 50) -> list[Dict[str, Any]]:
        """Get match history for a player with their MMR at match time."""
        # Get matches where player participated
        # Use contains operator to check if discord_id is in the arrays
        result = self.client.table("matches").select(
            "id, match_id, created_at, winning_team, team1_player_ids, team2_player_ids, player_mmrs, mmr_change"
        ).or_(
            f"team1_player_ids.cs.{{{discord_id}}},team2_player_ids.cs.{{{discord_id}}}"
        ).order("created_at", desc=True).limit(limit).execute()
        
        matches = []
        for match in (result.data if result.data else []):
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
    
    async def get_mmr_leaderboard(self, limit: int = 20) -> list[Dict[str, Any]]:
        """Get MMR leaderboard sorted by custom_mmr."""
        # Get users with league accounts, ordered by MMR
        # Use inner join to only get users with connected league accounts
        result = self.client.table("users").select(
            "discord_id, username, custom_mmr, league_accounts(game_name, tag_line, highest_tier, highest_rank)"
        ).order("custom_mmr", desc=True).limit(limit).execute()
        
        leaderboard = []
        for user in (result.data if result.data else []):
            # Skip users without league accounts
            league_accounts = user.get("league_accounts", [])
            if not league_accounts:
                continue
            
            # Get first league account (users should only have one)
            league_account = league_accounts[0] if isinstance(league_accounts, list) else league_accounts
            
            leaderboard.append({
                "discord_id": user["discord_id"],
                "username": user.get("username", "Unknown"),
                "custom_mmr": user.get("custom_mmr", 1000),
                "game_name": league_account.get("game_name") if isinstance(league_account, dict) else None,
                "tag_line": league_account.get("tag_line") if isinstance(league_account, dict) else None,
                "highest_tier": league_account.get("highest_tier") if isinstance(league_account, dict) else None,
                "highest_rank": league_account.get("highest_rank") if isinstance(league_account, dict) else None
            })
        
        return leaderboard

