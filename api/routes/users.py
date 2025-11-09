"""User management routes."""
from fastapi import APIRouter, HTTPException
from api.models.schemas import LeagueAccountConnect, LeagueAccountResponse
from api.services.database import DatabaseService
from api.services.riot_api import RiotAPIClient, RiotAPIError
from config import Config

router = APIRouter(prefix="/users", tags=["users"])
db_service = DatabaseService()
riot_client = RiotAPIClient()


@router.post("/connect", response_model=LeagueAccountResponse)
async def connect_league_account(account: LeagueAccountConnect):
    """
    Connect a Discord user to their League of Legends account.
    
    Fetches account information from Riot API and stores it in the database.
    """
    import logging
    import traceback
    logger = logging.getLogger("api")
    
    try:
        logger.info(f"[API] /connect called for Discord ID: {account.discord_id}, Riot ID: {account.game_name}#{account.tag_line}")
        
        # Get account info from Riot API
        logger.info(f"[API] Fetching account info from Riot API...")
        account_info = await riot_client.get_account_by_riot_id(
            account.game_name,
            account.tag_line
        )
        puuid = account_info.get("puuid")
        logger.info(f"[API] Got PUUID: {puuid}")
        
        if not puuid:
            logger.error(f"[API] ERROR: No PUUID found")
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Get highest tier
        logger.info(f"[API] Fetching highest tier...")
        highest_tier, highest_rank = await riot_client.get_highest_tier(
            account.game_name,
            account.tag_line
        )
        logger.info(f"[API] ⚠️ RETURNED VALUES - Tier: {highest_tier} (type: {type(highest_tier)}), Rank: {highest_rank} (type: {type(highest_rank)})")
        
        # Get or create user
        user = await db_service.get_or_create_user(
            account.discord_id,
            account.discord_username  # Store Discord username, not Riot username
        )
        
        # Upsert league account
        league_account = await db_service.upsert_league_account(
            discord_id=account.discord_id,
            game_name=account.game_name,
            tag_line=account.tag_line,
            puuid=puuid,
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
                tier_based_mmr = riot_client.tier_to_value(highest_tier, highest_rank)
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
            puuid=puuid,
            highest_tier=highest_tier,
            highest_rank=highest_rank,
            custom_mmr=custom_mmr
        )
        
    except RiotAPIError as e:
        logger.error(f"[API] RiotAPIError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
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

