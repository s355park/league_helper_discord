"""User management routes."""
from fastapi import APIRouter, HTTPException
from api.models.schemas import LeagueAccountConnect, LeagueAccountResponse
from api.services.database import DatabaseService
from api.services.tier_utils import tier_to_value
from config import Config

router = APIRouter(prefix="/users", tags=["users"])
db_service = DatabaseService()


@router.post("/connect", response_model=LeagueAccountResponse)
async def connect_league_account(account: LeagueAccountConnect):
    """
    Connect a Discord user to their League of Legends account.
    
    Stores account information in the database. Tier and rank can be provided manually.
    """
    import logging
    import traceback
    logger = logging.getLogger("api")
    
    try:
        logger.info(f"[API] /connect called for Discord ID: {account.discord_id}, Riot ID: {account.game_name}#{account.tag_line}")
        
        # Use provided tier/rank or None
        highest_tier = account.highest_tier
        highest_rank = account.highest_rank
        
        # Normalize tier to uppercase if provided
        if highest_tier:
            highest_tier = highest_tier.upper()
        
        # Normalize rank to uppercase if provided
        if highest_rank:
            highest_rank = highest_rank.upper()
        
        logger.info(f"[API] Using tier: {highest_tier}, rank: {highest_rank}")
        
        # Get or create user
        user = await db_service.get_or_create_user(
            account.discord_id,
            account.discord_username  # Store Discord username, not Riot username
        )
        
        # Upsert league account (puuid is None since we're not using Riot API)
        league_account = await db_service.upsert_league_account(
            discord_id=account.discord_id,
            game_name=account.game_name,
            tag_line=account.tag_line,
            puuid=None,  # No PUUID since we're not using Riot API
            highest_tier=highest_tier,
            highest_rank=highest_rank
        )
        
        # Get or create guild_user entry and get custom_mmr
        guild_user = await db_service.get_or_create_guild_user(account.guild_id, account.discord_id, 1000)
        custom_mmr = guild_user.get("custom_mmr", 1000)
        
        # If MMR is default (1000), calculate from tier
        if custom_mmr == 1000:
            if highest_tier:
                # Calculate MMR based on tier and rank
                tier_based_mmr = tier_to_value(highest_tier, highest_rank)
                logger.info(f"[API] Setting initial MMR from tier: {highest_tier} {highest_rank} = {tier_based_mmr}")
                
                # Update user's MMR in database (guild-specific)
                await db_service.update_player_mmr(account.discord_id, tier_based_mmr, account.guild_id)
                custom_mmr = tier_based_mmr
            else:
                # No tier available, use default
                custom_mmr = 1000
                logger.info(f"[API] No tier available, using default MMR: {custom_mmr}")
        else:
            logger.info(f"[API] User already has custom MMR: {custom_mmr}, keeping existing value")
        
        return LeagueAccountResponse(
            discord_id=account.discord_id,
            game_name=account.game_name,
            tag_line=account.tag_line,
            puuid=None,  # No PUUID since we're not using Riot API
            highest_tier=highest_tier,
            highest_rank=highest_rank,
            custom_mmr=custom_mmr
        )
        
    except ValueError as e:
        logger.error(f"[API] ValueError: {e}")
        # Handle database constraint violations (PUUID already connected)
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"[API] Exception in /connect: {e}")
        logger.error(f"[API] Full traceback:")
        import traceback
        logger.error(traceback.format_exc())
        error_msg = str(e)
        # Check if it's a database constraint error
        if "duplicate key" in error_msg or "unique constraint" in error_msg or "23505" in error_msg:
            if "puuid" in error_msg.lower():
                raise HTTPException(
                    status_code=409, 
                    detail="This League account is already connected to another Discord user"
                )
            else:
                raise HTTPException(
                    status_code=409,
                    detail="This account is already connected"
                )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/leaderboard")
async def get_leaderboard(guild_id: str, limit: int = 20):
    """Get MMR leaderboard for a specific guild."""
    leaderboard = await db_service.get_mmr_leaderboard(guild_id, limit)
    return {"leaderboard": leaderboard}


@router.get("/{discord_id}", response_model=LeagueAccountResponse)
async def get_user_account(discord_id: str, guild_id: str):
    """Get League account information for a Discord user in a specific guild."""
    account = await db_service.get_league_account(discord_id, guild_id)
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return LeagueAccountResponse(
        discord_id=account["discord_id"],
        game_name=account["game_name"],
        tag_line=account["tag_line"],
        puuid=account["puuid"],
        highest_tier=account.get("highest_tier"),
        highest_rank=account.get("highest_rank"),
        custom_mmr=account.get("custom_mmr", 1000)
    )


@router.get("/{discord_id}/match-history")
async def get_user_match_history(discord_id: str, guild_id: str, limit: int = 50):
    """Get match history for a user with MMR progression in a specific guild."""
    history = await db_service.get_player_match_history(discord_id, guild_id, limit)
    return {"matches": history}


@router.put("/{discord_id}/mmr")
async def modify_player_mmr(discord_id: str, guild_id: str, new_mmr: int):
    """
    Modify a player's MMR for a specific guild.
    
    Note: Permission checks should be done by the Discord bot (administrator only).
    """
    import logging
    logger = logging.getLogger("api")
    
    try:
        logger.info(f"[API] /modify-mmr called for Discord ID: {discord_id}, Guild ID: {guild_id}, New MMR: {new_mmr}")
        
        # Validate MMR value
        if new_mmr < 0:
            raise HTTPException(status_code=400, detail="MMR must be a positive integer (0 or greater)")
        
        # Check if account exists
        account = await db_service.get_league_account(discord_id, guild_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Get current MMR
        old_mmr = account.get("custom_mmr", 1000)
        
        # Update MMR
        await db_service.update_player_mmr(discord_id, new_mmr, guild_id)
        
        logger.info(f"[API] MMR updated: {discord_id} from {old_mmr} to {new_mmr}")
        
        return {
            "discord_id": discord_id,
            "old_mmr": old_mmr,
            "new_mmr": new_mmr,
            "message": f"MMR updated from {old_mmr} to {new_mmr}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Exception in /modify-mmr: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
