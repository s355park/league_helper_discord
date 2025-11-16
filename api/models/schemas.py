"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel
from typing import Optional, List


class LeagueAccountConnect(BaseModel):
    """Request schema for connecting a League account."""
    discord_id: str
    discord_username: str  # Discord username (display name)
    game_name: str
    tag_line: str
    guild_id: str  # Discord server (guild) ID
    highest_tier: Optional[str] = None  # Optional tier (e.g., "DIAMOND", "GOLD", "MASTER")
    highest_rank: Optional[str] = None  # Optional rank (e.g., "I", "II", "III", "IV") - not used for Master+


class LeagueAccountResponse(BaseModel):
    """Response schema for League account information."""
    discord_id: str
    game_name: str
    tag_line: str
    puuid: Optional[str]  # Optional since we're not using Riot API
    highest_tier: Optional[str]
    highest_rank: Optional[str]
    custom_mmr: int


class PlayerInfo(BaseModel):
    """Player information for team generation."""
    discord_id: str
    game_name: str
    tag_line: str
    tier_value: int  # Numeric value for tier comparison (from ranked tier)
    custom_mmr: int  # Custom MMR for balancing
    highest_tier: Optional[str] = None  # For display purposes
    highest_rank: Optional[str] = None  # For display purposes


class GenerateTeamsRequest(BaseModel):
    """Request schema for generating teams."""
    discord_ids: List[str]  # List of 10 Discord IDs
    guild_id: str  # Discord server (guild) ID


class Team(BaseModel):
    """Team representation."""
    players: List[PlayerInfo]
    total_tier_value: int


class GenerateTeamsResponse(BaseModel):
    """Response schema for generated teams."""
    team1: Team
    team2: Team
    tier_difference: int
    match_id: str  # Unique ID for this match (for recording results)


class MatchResultRequest(BaseModel):
    """Request schema for recording match results."""
    match_id: str
    winning_team: int  # 1 or 2
    team1_discord_ids: List[str]
    team2_discord_ids: List[str]
    guild_id: str  # Discord server (guild) ID


class MatchResultResponse(BaseModel):
    """Response schema for match result."""
    match_id: str
    winning_team: int
    mmr_changes: dict  # Map of discord_id -> mmr_change
    message: str

