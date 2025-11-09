"""FastAPI client wrapper for Discord bot."""
import httpx
from typing import Dict, Any, List
from config import Config


class APIClient:
    """Client for making requests to the FastAPI backend."""
    
    def __init__(self):
        self.base_url = Config.API_BASE_URL
    
    async def connect_account(
        self,
        discord_id: str,
        game_name: str,
        tag_line: str,
        guild_id: str
    ) -> Dict[str, Any]:
        """Connect a Discord user to their League account."""
        url = f"{self.base_url}/users/connect"
        data = {
            "discord_id": discord_id,
            "game_name": game_name,
            "tag_line": tag_line,
            "guild_id": guild_id
        }
        
        print(f"[Bot] Making request to {url}", flush=True)
        print(f"[Bot] Data: {data}", flush=True)
        
        try:
            async with httpx.AsyncClient() as client:
                print(f"[Bot] Sending POST request...", flush=True)
                response = await client.post(url, json=data, timeout=30.0)
                print(f"[Bot] Got response: {response.status_code}", flush=True)
                response.raise_for_status()
                result = response.json()
                print(f"[Bot] Response data: {result}", flush=True)
                return result
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to API at {url}. Error: {str(e)}\n\nIs the FastAPI server running? Try: python -m uvicorn api.main:app --reload")
        except httpx.TimeoutException:
            raise ConnectionError(f"Request to API timed out. The server may be overloaded.")
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
    
    async def get_user_account(self, discord_id: str, guild_id: str) -> Dict[str, Any]:
        """Get League account for a Discord user."""
        url = f"{self.base_url}/users/{discord_id}"
        params = {"guild_id": guild_id}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to API at {url}. Error: {str(e)}\n\nIs the FastAPI server running? Try: python -m uvicorn api.main:app --reload")
        except httpx.TimeoutException:
            raise ConnectionError(f"Request to API timed out. The server may be overloaded.")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise Exception("Account not found")
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
    
    async def generate_teams(self, discord_ids: List[str], guild_id: str) -> Dict[str, Any]:
        """Generate balanced teams from Discord user IDs."""
        url = f"{self.base_url}/teams/generate"
        data = {"discord_ids": discord_ids, "guild_id": guild_id}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=30.0)
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to API at {url}. Error: {str(e)}\n\nIs the FastAPI server running? Try: python -m uvicorn api.main:app --reload")
        except httpx.TimeoutException:
            raise ConnectionError(f"Request to API timed out. The server may be overloaded.")
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
    
    async def record_match_result(
        self,
        match_id: str,
        winning_team: int,
        team1_discord_ids: List[str],
        team2_discord_ids: List[str],
        guild_id: str
    ) -> Dict[str, Any]:
        """Record the result of a match and update player MMRs."""
        url = f"{self.base_url}/teams/match-result"
        data = {
            "match_id": match_id,
            "winning_team": winning_team,
            "team1_discord_ids": team1_discord_ids,
            "team2_discord_ids": team2_discord_ids,
            "guild_id": guild_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=30.0)
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to API at {url}. Error: {str(e)}\n\nIs the FastAPI server running? Try: python -m uvicorn api.main:app --reload")
        except httpx.TimeoutException:
            raise ConnectionError(f"Request to API timed out. The server may be overloaded.")
        except httpx.HTTPStatusError as e:
            raise Exception(f"API error: {e.response.status_code} - {e.response.text}")

