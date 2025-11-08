"""Discord bot entry point."""
import discord
from discord.ext import commands
import asyncio
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import Config

# Import commands
from bot.commands import connect, teams, attendance, mmr_history, leaderboard


class LeagueTeamBot(commands.Bot):
    """Main Discord bot class."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            description="League of Legends Team Generator Bot"
        )
    
    async def setup_hook(self):
        """Called when the bot is being set up."""
        # Register commands
        await self.add_cog(connect.ConnectCommand(self))
        await self.add_cog(teams.TeamsCommand(self))
        await self.add_cog(attendance.AttendanceCommand(self))
        await self.add_cog(mmr_history.MMRHistoryCommand(self))
        await self.add_cog(leaderboard.LeaderboardCommand(self))
        
        # Sync commands globally (available to all guilds)
        try:
            synced = await self.tree.sync()
            print(f"✅ Synced {len(synced)} command(s) globally")
            for cmd in synced:
                print(f"   - {cmd.name}")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")
            import traceback
            traceback.print_exc()
    
    async def on_ready(self):
        """Called when the bot is ready."""
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"Bot is ready! Connected to {len(self.guilds)} guild(s)")
        print(f"API Base URL: {Config.API_BASE_URL}")
        print(f"FastAPI should be running at: {Config.API_BASE_URL}")
        
        # Clear any existing guild-specific commands to avoid duplicates
        # (Global commands will be available to all guilds)
        print("\n🧹 Clearing duplicate guild-specific commands...")
        for guild in self.guilds:
            try:
                self.tree.clear_commands(guild=guild)
                await self.tree.sync(guild=guild)
                print(f"   ✅ Cleared duplicates in '{guild.name}'")
            except Exception as e:
                print(f"   ⚠️ Could not clear commands in '{guild.name}': {e}")
    
    async def on_command_error(self, ctx, error):
        """Handle command errors."""
        if isinstance(error, commands.CommandNotFound):
            return
        print(f"Error: {error}")


async def main():
    """Main function to run the bot."""
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file")
        sys.exit(1)
    
    # Create and run bot
    bot = LeagueTeamBot()
    
    try:
        await bot.start(Config.DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("Invalid Discord bot token. Please check your .env file.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Bot shutting down...")
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())

