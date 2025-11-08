"""Riot Games API client for fetching League of Legends player data."""
import httpx
from typing import Optional, Dict, Any
from urllib.parse import quote
from config import Config


class RiotAPIError(Exception):
    """Custom exception for Riot API errors."""
    pass


class RiotAPIClient:
    """Client for interacting with Riot Games API."""
    
    # Tier ranking values (higher is better)
    TIER_VALUES = {
        "IRON": 1,
        "BRONZE": 2,
        "SILVER": 3,
        "GOLD": 4,
        "PLATINUM": 5,
        "EMERALD": 6,
        "DIAMOND": 7,
        "MASTER": 8,
        "GRANDMASTER": 9,
        "CHALLENGER": 10,
    }
    
    # Rank values within tier (higher = better)
    # Each rank = 1 unit, will be multiplied by 25 to get MMR bonus
    RANK_VALUES = {
        "I": 3,    # +75 MMR (3 * 25)
        "II": 2,   # +50 MMR (2 * 25)
        "III": 1,  # +25 MMR (1 * 25)
        "IV": 0,   # +0 MMR (0 * 25)
    }
    
    def __init__(self):
        self.api_key = Config.RIOT_API_KEY
        self.base_url = Config.RIOT_API_BASE_URL
        self.headers = {
            "X-Riot-Token": self.api_key
        }
    
    async def get_account_by_riot_id(self, game_name: str, tag_line: str) -> Dict[str, Any]:
        """
        Get account information by Riot ID (gameName#tagLine).
        
        Args:
            game_name: The game name (username)
            tag_line: The tag line (discriminator)
            
        Returns:
            Account information including PUUID
            
        Raises:
            RiotAPIError: If API call fails
        """
        # URL encode the game name and tag line to handle special characters
        encoded_game_name = quote(game_name, safe='')
        encoded_tag_line = quote(tag_line, safe='')
        url = f"{self.base_url}/riot/account/v1/accounts/by-riot-id/{encoded_game_name}/{encoded_tag_line}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise RiotAPIError(f"Account not found: {game_name}#{tag_line}")
                elif e.response.status_code == 403:
                    raise RiotAPIError("Invalid Riot API key")
                else:
                    raise RiotAPIError(f"Riot API error: {e.response.status_code}")
            except httpx.RequestError as e:
                raise RiotAPIError(f"Request failed: {str(e)}")
    
    async def get_summoner_by_puuid(self, puuid: str, region: str = "na1") -> Dict[str, Any]:
        """
        Get summoner information by PUUID.
        
        Args:
            puuid: Player's PUUID
            region: Region code (default: na1)
            
        Returns:
            Summoner information including summoner ID
            
        Raises:
            RiotAPIError: If API call fails
        """
        regional_base = self._get_regional_base_url(region)
        url = f"{regional_base}/lol/summoner/v4/summoners/by-puuid/{puuid}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise RiotAPIError("Summoner not found")
                raise RiotAPIError(f"Riot API error: {e.response.status_code}")
            except httpx.RequestError as e:
                raise RiotAPIError(f"Request failed: {str(e)}")
    
    async def get_ranked_data(self, summoner_id: str, region: str = "na1") -> list[Dict[str, Any]]:
        """
        Get ranked data for a player by summoner ID.
        
        DEPRECATED: Use get_ranked_data_by_puuid instead.
        
        Args:
            summoner_id: Player's summoner ID
            region: Region code (default: na1)
            
        Returns:
            List of ranked data entries
            
        Raises:
            RiotAPIError: If API call fails
        """
        # Determine regional API base URL
        regional_base = self._get_regional_base_url(region)
        url = f"{regional_base}/lol/league/v4/entries/by-summoner/{summoner_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # Player might not have ranked data
                    return []
                raise RiotAPIError(f"Riot API error: {e.response.status_code}")
            except httpx.RequestError as e:
                raise RiotAPIError(f"Request failed: {str(e)}")
    
    async def get_ranked_data_by_puuid(self, puuid: str, region: str = "na1") -> list[Dict[str, Any]]:
        """
        Get ranked data for a player by PUUID.
        
        Args:
            puuid: Player's encrypted PUUID
            region: Region code (default: na1)
            
        Returns:
            List of ranked data entries
            
        Raises:
            RiotAPIError: If API call fails
        """
        # Determine regional API base URL
        regional_base = self._get_regional_base_url(region)
        url = f"{regional_base}/lol/league/v4/entries/by-puuid/{puuid}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    # Player might not have ranked data
                    return []
                raise RiotAPIError(f"Riot API error: {e.response.status_code}")
            except httpx.RequestError as e:
                raise RiotAPIError(f"Request failed: {str(e)}")
    
    def _get_regional_base_url(self, region: str) -> str:
        """Get the regional API base URL."""
        regional_map = {
            "na1": "https://na1.api.riotgames.com",
            "euw1": "https://euw1.api.riotgames.com",
            "eun1": "https://eun1.api.riotgames.com",
            "kr": "https://kr.api.riotgames.com",
            "br1": "https://br1.api.riotgames.com",
            "la1": "https://la1.api.riotgames.com",
            "la2": "https://la2.api.riotgames.com",
            "oc1": "https://oc1.api.riotgames.com",
            "tr1": "https://tr1.api.riotgames.com",
            "ru": "https://ru.api.riotgames.com",
            "jp1": "https://jp1.api.riotgames.com",
            "ph2": "https://ph2.api.riotgames.com",
            "sg2": "https://sg2.api.riotgames.com",
            "th2": "https://th2.api.riotgames.com",
            "tw2": "https://tw2.api.riotgames.com",
            "vn2": "https://vn2.api.riotgames.com",
        }
        return regional_map.get(region.lower(), "https://na1.api.riotgames.com")
    
    def _guess_region_from_tag(self, tag_line: str) -> Optional[str]:
        """Try to guess the region from the tag line."""
        tag_lower = tag_line.upper()
        # Map common tag patterns to regions
        tag_to_region = {
            "NA1": "na1", "NA": "na1",
            "EUW": "euw1", "EUW1": "euw1",
            "EUN": "eun1", "EUN1": "eun1",
            "KR": "kr", "KR1": "kr",
            "BR": "br1", "BR1": "br1",
            "LAN": "la1", "LA1": "la1",
            "LAS": "la2", "LA2": "la2",
            "OCE": "oc1", "OC1": "oc1",
            "TR": "tr1", "TR1": "tr1",
            "RU": "ru",
            "JP": "jp1", "JP1": "jp1",
        }
        return tag_to_region.get(tag_lower)
    
    async def get_highest_tier(self, game_name: str, tag_line: str, region: str = "na1") -> tuple[Optional[str], Optional[str]]:
        """
        Get the highest tier and rank for a player (current highest across all queues).
        
        Note: Riot API doesn't directly provide historical "highest ever" rank.
        This method returns the highest current rank across all ranked queues.
        For true historical data, match history analysis would be required.
        
        Args:
            game_name: The game name
            tag_line: The tag line
            region: Region code (default: na1 for North America)
            
        Returns:
            Tuple of (highest_tier, highest_rank) or (None, None) if not found
        """
        import logging
        logger = logging.getLogger("api")
        
        try:
            # Get account info
            account = await self.get_account_by_riot_id(game_name, tag_line)
            puuid = account.get("puuid")
            
            if not puuid:
                print(f"[RiotAPI] No PUUID found for {game_name}#{tag_line}")
                return None, None
            
            # Get ranked data directly by PUUID
            ranked_data = await self.get_ranked_data_by_puuid(puuid, region)
            
            logger.info(f"[RiotAPI] Ranked data returned: {ranked_data}")
            
            if not ranked_data:
                logger.warning(f"[RiotAPI] No ranked data found for {game_name}#{tag_line} in region {region}")
                return None, None
            
            logger.info(f"[RiotAPI] Found ranked data in region {region}: {len(ranked_data)} entries")
            
            # Find highest tier across all queues
            highest_tier = None
            highest_rank = None
            highest_value = 0
            
            for entry in ranked_data:
                tier = entry.get("tier", "")
                rank = entry.get("rank", "")
                queue_type = entry.get("queueType", "")
                
                print(f"[RiotAPI] Processing entry: queue={queue_type}, tier={tier}, rank={rank}")
                
                if tier:
                    tier_upper = tier.upper()
                    if tier_upper in self.TIER_VALUES:
                        tier_value = self.TIER_VALUES[tier_upper]
                        rank_value = self.RANK_VALUES.get(rank, 2)
                        # Combined value: tier * 10 + (5 - rank_value) for better sorting
                        combined_value = tier_value * 10 + (5 - rank_value)
                        
                        print(f"[RiotAPI] Tier value: {tier_upper}={tier_value}, Rank={rank}={rank_value}, Combined={combined_value}")
                        
                        if combined_value > highest_value:
                            highest_value = combined_value
                            highest_tier = tier_upper
                            highest_rank = rank
                            print(f"[RiotAPI] New highest: {highest_tier} {highest_rank} in {queue_type}")
                    else:
                        print(f"[RiotAPI] WARNING - Tier '{tier}' not in TIER_VALUES: {list(self.TIER_VALUES.keys())}")
                else:
                    print(f"[RiotAPI] WARNING - Entry has no tier field: {entry}")
            
            if highest_tier:
                logger.info(f"[RiotAPI] SUCCESS - Final highest tier: {highest_tier} {highest_rank}")
            else:
                logger.warning(f"[RiotAPI] ERROR - No valid tier found in ranked data for {game_name}#{tag_line}")
            
            logger.info(f"[RiotAPI] RETURNING: tier={highest_tier}, rank={highest_rank}")
            return highest_tier, highest_rank
            
        except RiotAPIError as e:
            logger.error(f"[RiotAPI] RiotAPIError in get_highest_tier: {str(e)}")
            return None, None
        except Exception as e:
            logger.error(f"[RiotAPI] Unexpected error in get_highest_tier: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None
    
    def tier_to_value(self, tier: Optional[str], rank: Optional[str] = None) -> int:
        """
        Convert tier and rank to a numeric value for team balancing.
        
        Each tier = 100 points, each division = 25 points
        This matches League's ~100 LP per division structure.
        
        Args:
            tier: Tier name (e.g., "DIAMOND", "GOLD")
            rank: Rank within tier (e.g., "I", "II", "III", "IV")
            
        Returns:
            Numeric value representing skill level
        """
        if not tier:
            return 0
        
        tier_val = self.TIER_VALUES.get(tier.upper(), 0)
        base_mmr = tier_val * 100  # Each tier = 100 points
        
        if rank:
            # Each division = 25 points (I=75, II=50, III=25, IV=0)
            rank_bonus = self.RANK_VALUES.get(rank.upper(), 0) * 25
            return base_mmr + rank_bonus
        
        return base_mmr

