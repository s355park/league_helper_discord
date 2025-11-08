"""Test script to verify Supabase database connection and schema."""
import asyncio
import sys
import os
from supabase import create_client
from config import Config

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def test_connection():
    """Test database connection and verify tables exist."""
    try:
        Config.validate()
    except ValueError as e:
        print(f"[ERROR] Configuration error: {e}")
        print("Please check your .env file")
        print(f"\nCurrent SUPABASE_URL: {Config.SUPABASE_URL or 'NOT SET'}")
        print(f"Current SUPABASE_KEY: {'SET' if Config.SUPABASE_KEY else 'NOT SET'}")
        return
    
    try:
        print(f"Connecting to Supabase URL: {Config.SUPABASE_URL}")
        client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        
        # Test connection by checking if tables exist
        print("Testing Supabase connection...")
        
        # Check users table
        result = client.table("users").select("discord_id").limit(1).execute()
        print("[SUCCESS] Successfully connected to 'users' table")
        
        # Check league_accounts table
        result = client.table("league_accounts").select("discord_id").limit(1).execute()
        print("[SUCCESS] Successfully connected to 'league_accounts' table")
        
        print("\n[SUCCESS] Database connection successful! All tables are accessible.")
        print(f"Project URL: {Config.SUPABASE_URL}")
        
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        print("\nPlease verify:")
        print("1. Your .env file has correct SUPABASE_URL and SUPABASE_KEY")
        print("2. The migration was applied successfully")
        print("3. Your Supabase project is active (not paused)")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())


