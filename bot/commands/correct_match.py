"""Correct match result command."""
import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.api_client import APIClient
import httpx


class CorrectMatchCommand(commands.Cog):
    """Command to correct a match result that was recorded incorrectly."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_client = APIClient()
    
    @app_commands.command(name="correct-match-result", description="Correct a match result after clicking the wrong team won")
    @app_commands.describe(
        match_id="The match ID to correct (found in the match result message)",
        winning_team="The correct winning team (1 or 2)"
    )
    async def correct_match_result(
        self,
        interaction: discord.Interaction,
        match_id: str,
        winning_team: int
    ):
        """Correct a match result that was recorded incorrectly."""
        if not interaction.guild_id:
            await interaction.response.send_message(
                "This command can only be used in a server!",
                ephemeral=True
            )
            return
        
        # Validate winning_team
        if winning_team not in [1, 2]:
            embed = discord.Embed(
                title="❌ Invalid Team",
                description="Winning team must be 1 or 2.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(thinking=True)
        
        try:
            # Call API to correct match result
            result = await self.api_client.correct_match_result(
                match_id,
                winning_team,
                str(interaction.guild_id)
            )
            
            embed = discord.Embed(
                title="✅ Match Result Corrected",
                description=result["message"],
                color=discord.Color.green()
            )
            
            # Show MMR changes
            mmr_text = ""
            mmr_changes = result.get("mmr_changes", {})
            
            # Group by team (we need to get team info from the match, but for now just show all)
            if mmr_changes:
                # Show positive changes first (winners)
                winners = [discord_id for discord_id, change in mmr_changes.items() if change > 0]
                losers = [discord_id for discord_id, change in mmr_changes.items() if change < 0]
                
                if winners:
                    mmr_text += "**Winners:**\n"
                    for discord_id in winners:
                        change = mmr_changes[discord_id]
                        mmr_text += f"<@{discord_id}>: **+{change}** MMR\n"
                    mmr_text += "\n"
                
                if losers:
                    mmr_text += "**Losers:**\n"
                    for discord_id in losers:
                        change = mmr_changes[discord_id]
                        mmr_text += f"<@{discord_id}>: **{change}** MMR\n"
            
            if mmr_text:
                embed.add_field(name="MMR Changes", value=mmr_text, inline=False)
            
            embed.set_footer(text=f"Match ID: {match_id}")
            
            await interaction.followup.send(embed=embed)
            
        except httpx.HTTPStatusError as e:
            error_msg = f"API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "detail" in error_data:
                    error_msg = error_data["detail"]
            except:
                error_msg = e.response.text
            
            embed = discord.Embed(
                title="❌ Error Correcting Match",
                description=error_msg,
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except ConnectionError as e:
            error_msg = str(e)
            embed = discord.Embed(
                title="❌ Connection Error",
                description=f"{error_msg}\n\n**Make sure the FastAPI server is running:**\n```powershell\npython -m uvicorn api.main:app --reload\n```",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            error_msg = str(e)
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to correct match result: {error_msg}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            import traceback
            traceback.print_exc()


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(CorrectMatchCommand(bot))

