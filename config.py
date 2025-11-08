"""Configuration management for the Discord League Team Generator."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Discord Bot
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    
    # Riot Games API
    RIOT_API_KEY = os.getenv("RIOT_API_KEY")
    RIOT_API_BASE_URL = os.getenv("RIOT_API_BASE_URL", "https://americas.api.riotgames.com")
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # FastAPI
    API_HOST = os.getenv("API_HOST", "0.0.0.0")  # For server binding
    # PORT is set by cloud providers (Render, Railway, etc.)
    API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", 8000)))
    # Use localhost for client connections (0.0.0.0 is not a valid client address)
    API_BASE_URL = f"http://127.0.0.1:{API_PORT}"
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        required = [
            "DISCORD_BOT_TOKEN",
            "RIOT_API_KEY",
            "SUPABASE_URL",
            "SUPABASE_KEY",
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

