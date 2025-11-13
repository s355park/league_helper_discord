"""Team generation routes."""
from fastapi import APIRouter, HTTPException
from api.models.schemas import (
    GenerateTeamsRequest, GenerateTeamsResponse, PlayerInfo, Team,
    MatchResultRequest, MatchResultResponse
)
from api.services.database import DatabaseService
from api.utils.mmr_calculator import tier_to_value
from api.services.team_balancer import TeamBalancer
import uuid

router = APIRouter(prefix="/teams", tags=["teams"])
db_service = DatabaseService()
team_balancer = TeamBalancer()


@router.post("/generate", response_model=GenerateTeamsResponse)
async def generate_teams(request: GenerateTeamsRequest):
    """
    Generate balanced teams from 10 Discord user IDs.
    
    Requires all 10 players to have connected their League accounts.
    """
    if len(request.discord_ids) != 10:
        raise HTTPException(
            status_code=400,
            detail="Exactly 10 Discord IDs are required"
        )
    
    # Get all player accounts from database with guild-specific MMR
    accounts = await db_service.get_players_by_discord_ids(request.discord_ids, request.guild_id)
    
    if len(accounts) != 10:
        missing = set(request.discord_ids) - {acc["discord_id"] for acc in accounts}
        raise HTTPException(
            status_code=400,
            detail=f"Some players have not connected their accounts: {', '.join(missing)}"
        )
    
    # Convert to PlayerInfo objects with tier values and custom MMR
    players = []
    for account in accounts:
        tier_value = tier_to_value(
            account.get("highest_tier"),
            account.get("highest_rank")
        )
        
        players.append(PlayerInfo(
            discord_id=account["discord_id"],
            game_name=account["game_name"],
            tag_line=account["tag_line"],
            tier_value=tier_value,
            custom_mmr=account.get("custom_mmr", 1000),
            highest_tier=account.get("highest_tier"),
            highest_rank=account.get("highest_rank")
        ))
    
    # Generate balanced teams
    team1, team2 = team_balancer.generate_balanced_teams(players)
    
    # Calculate tier difference
    tier_difference = team_balancer.calculate_tier_difference(team1, team2)
    
    # Generate unique match ID
    match_id = str(uuid.uuid4())
    
    return GenerateTeamsResponse(
        team1=team1,
        team2=team2,
        tier_difference=tier_difference,
        match_id=match_id
    )


@router.post("/match-result", response_model=MatchResultResponse)
async def record_match_result(result: MatchResultRequest):
    """
    Record the result of a match and update player MMRs.
    
    Args:
        result: Match result with winning team and player IDs
        
    Returns:
        Match result response with MMR changes
    """
    from api.services.mmr_calculator import MMRCalculator
    
    if result.winning_team not in [1, 2]:
        raise HTTPException(
            status_code=400,
            detail="winning_team must be 1 or 2"
        )
    
    # Get current MMRs for all players with guild-specific MMR
    all_discord_ids = result.team1_discord_ids + result.team2_discord_ids
    accounts = await db_service.get_players_by_discord_ids(all_discord_ids, result.guild_id)
    
    if len(accounts) != 10:
        raise HTTPException(
            status_code=400,
            detail="Could not find all player accounts"
        )
    
    # Build MMR maps
    mmr_map = {acc["discord_id"]: acc.get("custom_mmr", 1000) for acc in accounts}
    team1_mmrs = [mmr_map[discord_id] for discord_id in result.team1_discord_ids]
    team2_mmrs = [mmr_map[discord_id] for discord_id in result.team2_discord_ids]
    
    # Calculate MMR changes
    team1_avg = sum(team1_mmrs) / len(team1_mmrs)
    team2_avg = sum(team2_mmrs) / len(team2_mmrs)
    
    mmr_calculator = MMRCalculator()
    team1_actual_score = 1.0 if result.winning_team == 1 else 0.0
    team1_change = mmr_calculator.calculate_mmr_change(
        team1_avg, team2_avg, team1_actual_score
    )
    team2_change = -team1_change
    
    # Update MMRs for all players (guild-specific)
    mmr_changes = {}
    for discord_id in result.team1_discord_ids:
        new_mmr = mmr_map[discord_id] + team1_change
        await db_service.update_player_mmr(discord_id, new_mmr, result.guild_id)
        mmr_changes[discord_id] = team1_change
    
    for discord_id in result.team2_discord_ids:
        new_mmr = mmr_map[discord_id] + team2_change
        await db_service.update_player_mmr(discord_id, new_mmr, result.guild_id)
        mmr_changes[discord_id] = team2_change
    
    # Record match in database with player MMRs (before match)
    await db_service.record_match(
        match_id=result.match_id,
        team1_player_ids=result.team1_discord_ids,
        team2_player_ids=result.team2_discord_ids,
        winning_team=result.winning_team,
        team1_avg_mmr=int(team1_avg),
        team2_avg_mmr=int(team2_avg),
        mmr_change=abs(team1_change),
        guild_id=result.guild_id,
        player_mmrs=mmr_map  # Store MMRs before the match
    )
    
    winning_team_name = f"Team {result.winning_team}"
    message = f"{winning_team_name} won! MMR updated: {'+' if team1_change > 0 else ''}{team1_change} for Team 1, {'+' if team2_change > 0 else ''}{team2_change} for Team 2"
    
    return MatchResultResponse(
        match_id=result.match_id,
        winning_team=result.winning_team,
        mmr_changes=mmr_changes,
        message=message
    )

