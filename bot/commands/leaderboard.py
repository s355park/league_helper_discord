"""Leaderboard command to show MMR rankings."""
import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.api_client import APIClient
import httpx


class LeaderboardCommand(commands.Cog):
    """Command to view MMR leaderboard."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_client = APIClient()
    
    @app_commands.command(name="leaderboard", description="View MMR leaderboard")
    @app_commands.describe(limit="Number of players to show (default: 20, max: 50)")
    async def leaderboard(self, interaction: discord.Interaction, limit: int = 20):
        """Display MMR leaderboard."""
        await interaction.response.defer(thinking=True)
        
        if not interaction.guild_id:
            await interaction.followup.send("This command can only be used in a server!", ephemeral=True)
            return
        
        # Clamp limit
        limit = max(1, min(limit, 50))
        
        try:
            # Get leaderboard from API
            url = f"{self.api_client.base_url}/users/leaderboard"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params={"guild_id": str(interaction.guild_id), "limit": limit}, timeout=10.0)
                response.raise_for_status()
                data = response.json()
            
            leaderboard = data.get("leaderboard", [])
            
            if not leaderboard:
                embed = discord.Embed(
                    title="🏆 MMR Leaderboard",
                    description="No players found!",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Build leaderboard text
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉"]
            
            for i, player in enumerate(leaderboard, 1):
                rank_emoji = medals[i - 1] if i <= 3 else f"**{i}.**"
                
                username = player.get("username", "Unknown")
                game_name = player.get("game_name")
                mmr = player.get("custom_mmr", 1000)
                
                # Format tier display
                tier = player.get("highest_tier")
                rank = player.get("highest_rank")
                if tier and tier != "UNRANKED":
                    tier_display = f"{tier} {rank}".strip() if rank else tier
                else:
                    tier_display = "Unranked"
                
                # Try to mention user if possible, otherwise show username
                try:
                    user_id = int(player["discord_id"])
                    user_mention = f"<@{user_id}>"
                except:
                    user_mention = username
                
                # Add game name if available
                if game_name:
                    display_name = f"{user_mention} ({game_name})"
                else:
                    display_name = user_mention
                
                # Get winrate info
                winrate = player.get("winrate", 0.0)
                wins = player.get("wins", 0)
                losses = player.get("losses", 0)
                total_matches = player.get("total_matches", 0)
                
                # Format winrate display
                if total_matches > 0:
                    winrate_display = f"Winrate: **{winrate:.1f}%** ({wins}W-{losses}L)"
                else:
                    winrate_display = "Winrate: **N/A** (0 matches)"
                
                leaderboard_text += f"{rank_emoji} {display_name}\n"
                leaderboard_text += f"   MMR: **{mmr}** | Tier: {tier_display} | {winrate_display}\n\n"
            
            # Create embed
            embed = discord.Embed(
                title="🏆 MMR Leaderboard",
                description=leaderboard_text,
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"Showing top {len(leaderboard)} players")
            
            # Check if user is on leaderboard
            user_rank = None
            for i, player in enumerate(leaderboard, 1):
                if player["discord_id"] == str(interaction.user.id):
                    user_rank = i
                    break
            
            if user_rank:
                user_player = leaderboard[user_rank-1]
                user_mmr = user_player['custom_mmr']
                user_winrate = user_player.get("winrate", 0.0)
                user_wins = user_player.get("wins", 0)
                user_losses = user_player.get("losses", 0)
                user_total = user_player.get("total_matches", 0)
                
                if user_total > 0:
                    winrate_info = f" | Winrate: **{user_winrate:.1f}%** ({user_wins}W-{user_losses}L)"
                else:
                    winrate_info = " | Winrate: **N/A**"
                
                embed.add_field(
                    name="Your Rank",
                    value=f"You are ranked **#{user_rank}** with **{user_mmr}** MMR{winrate_info}",
                    inline=False
                )
            else:
                # Get user's MMR to show their rank
                try:
                    account = await self.api_client.get_user_account(str(interaction.user.id), str(interaction.guild_id))
                    user_mmr = account.get("custom_mmr", 1000)
                    
                    # Count how many players have higher MMR
                    rank = sum(1 for p in leaderboard if p.get("custom_mmr", 1000) > user_mmr) + 1
                    
                    embed.add_field(
                        name="Your Rank",
                        value=f"You are ranked **#{rank}+** with **{user_mmr}** MMR",
                        inline=False
                    )
                except:
                    pass
            
            await interaction.followup.send(embed=embed)
            
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
                description=f"Failed to fetch leaderboard: {error_msg}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            import traceback
            traceback.print_exc()


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(LeaderboardCommand(bot))

