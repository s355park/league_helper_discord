"""MMR accuracy check command with graph visualization."""
import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.api_client import APIClient
import httpx
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import io
from datetime import datetime


class MMRAccuracyCommand(commands.Cog):
    """Command to check MMR accuracy by analyzing how often higher MMR teams win."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_client = APIClient()
    
    @app_commands.command(name="check-mmr-accuracy", description="Check how often the team with higher MMR wins over time")
    async def check_mmr_accuracy(self, interaction: discord.Interaction):
        """Display MMR accuracy graph showing win rate of higher MMR teams over time."""
        await interaction.response.defer(thinking=True)
        
        if not interaction.guild_id:
            await interaction.followup.send("This command can only be used in a server!", ephemeral=True)
            return
        
        try:
            # Get MMR accuracy data from API
            url = f"{self.api_client.base_url}/teams/mmr-accuracy"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params={"guild_id": str(interaction.guild_id)}, timeout=30.0)
                response.raise_for_status()
                data = response.json()
            
            matches_analyzed = data.get("matches_analyzed", 0)
            overall_win_rate = data.get("overall_win_rate", 0.0)
            data_points = data.get("data_points", [])
            
            if matches_analyzed == 0:
                embed = discord.Embed(
                    title="📊 MMR Accuracy",
                    description="No matches found to analyze!\n\nPlay some games and record results to see MMR accuracy.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Prepare data for graphs
            match_numbers = [dp["match_number"] for dp in data_points]
            win_rates = [dp["cumulative_win_rate"] for dp in data_points]
            
            player_win_rate_data = data.get("player_win_rate_data", [])
            
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
            
            # Left graph: Higher MMR team win rate over time
            ax1.plot(match_numbers, win_rates, linewidth=2, color='#5865F2', marker='o', markersize=4, alpha=0.7)
            ax1.axhline(y=50, color='#ED4245', linestyle='--', linewidth=1.5, alpha=0.5, label='50% (Perfect Balance)')
            ax1.axhline(y=overall_win_rate, color='#57F287', linestyle='--', linewidth=1.5, alpha=0.5, label=f'Overall: {overall_win_rate:.1f}%')
            ax1.set_xlabel('Match #', fontsize=11, color='white')
            ax1.set_ylabel('Win Rate (%)', fontsize=11, color='white')
            ax1.set_title('Higher MMR Team Win Rate Over Time', fontsize=13, fontweight='bold', color='white', pad=15)
            ax1.set_ylim(0, 100)
            ax1.grid(True, alpha=0.3, linestyle='--')
            ax1.legend(loc='best', facecolor='#2F3136', edgecolor='white', labelcolor='white', fontsize=9)
            
            # Right graph: Average player win rate per 5-game bucket
            if player_win_rate_data:
                bucket_numbers = [b["bucket_number"] for b in player_win_rate_data]
                avg_win_rates = [b["average_win_rate"] for b in player_win_rate_data]
                min_win_rates = [b["min_win_rate"] for b in player_win_rate_data]
                max_win_rates = [b["max_win_rate"] for b in player_win_rate_data]
                
                # Plot average line
                ax2.plot(bucket_numbers, avg_win_rates, linewidth=2, color='#5865F2', marker='o', markersize=5, label='Average Win Rate', alpha=0.8)
                
                # Plot min/max as shaded area
                ax2.fill_between(bucket_numbers, min_win_rates, max_win_rates, alpha=0.2, color='#5865F2', label='Range (Min-Max)')
                
                # Add 50% reference line
                ax2.axhline(y=50, color='#57F287', linestyle='--', linewidth=1.5, alpha=0.7, label='50% (Ideal)')
                
                ax2.set_xlabel('5-Game Bucket #', fontsize=11, color='white')
                ax2.set_ylabel('Win Rate (%)', fontsize=11, color='white')
                ax2.set_title('Average Player Win Rate (per 5 games)', fontsize=13, fontweight='bold', color='white', pad=15)
                ax2.set_ylim(0, 100)
                ax2.grid(True, alpha=0.3, linestyle='--')
                ax2.legend(loc='best', facecolor='#2F3136', edgecolor='white', labelcolor='white', fontsize=9)
                
                # Add note about convergence
                if len(avg_win_rates) > 1:
                    first_avg = avg_win_rates[0]
                    last_avg = avg_win_rates[-1]
                    distance_from_50_first = abs(first_avg - 50)
                    distance_from_50_last = abs(last_avg - 50)
                    
                    if distance_from_50_last < distance_from_50_first:
                        convergence_note = f"✅ Converging to 50%"
                    else:
                        convergence_note = f"⚠️ Not converging"
                    
                    ax2.text(0.02, 0.02, convergence_note, 
                           transform=ax2.transAxes, fontsize=9, 
                           verticalalignment='bottom', color='white',
                           bbox=dict(boxstyle='round', facecolor='#2F3136', alpha=0.8))
            else:
                ax2.text(0.5, 0.5, 'Not enough player data\n(Need players with 5+ matches)', 
                        transform=ax2.transAxes, fontsize=12, 
                        ha='center', va='center', color='white')
                ax2.set_title('Average Player Win Rate (per 5 games)', fontsize=13, fontweight='bold', color='white', pad=15)
            
            # Set dark theme for both subplots
            fig.patch.set_facecolor('#2F3136')
            for ax in [ax1, ax2]:
                ax.set_facecolor('#36393F')
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['right'].set_color('white')
                ax.spines['left'].set_color('white')
            
            # Add statistics text to left graph
            stats_text = f'Matches: {matches_analyzed}\nWin Rate: {overall_win_rate:.1f}%'
            ax1.text(0.02, 0.98, stats_text, 
                   transform=ax1.transAxes, fontsize=10, 
                   verticalalignment='top', color='white',
                   bbox=dict(boxstyle='round', facecolor='#2F3136', alpha=0.8))
            
            plt.tight_layout()
            
            # Save to bytes
            buf = io.BytesIO()
            try:
                plt.savefig(buf, format='png', facecolor='#2F3136', dpi=100, bbox_inches='tight')
                buf.seek(0)
                plt.close()
            except Exception as e:
                plt.close()
                raise
            
            # Create embed
            embed = discord.Embed(
                title="📊 MMR Accuracy Analysis",
                description=f"Analyzed **{matches_analyzed}** matches\n\n**Overall Win Rate:** {overall_win_rate:.1f}%\n*Percentage of matches where the team with higher average MMR won*",
                color=discord.Color.blue()
            )
            
            # Add interpretation
            if overall_win_rate > 60:
                interpretation = "✅ MMR is working well! Higher MMR teams win significantly more often."
            elif overall_win_rate > 50:
                interpretation = "✅ MMR is reasonably accurate. Higher MMR teams win more often than not."
            elif overall_win_rate > 40:
                interpretation = "⚠️ MMR accuracy is moderate. Consider reviewing the MMR calculation."
            else:
                interpretation = "❌ MMR accuracy is low. The MMR system may need adjustment."
            
            embed.add_field(name="Interpretation", value=interpretation, inline=False)
            embed.set_image(url="attachment://mmr_accuracy.png")
            embed.set_footer(text=f"Based on {matches_analyzed} matches in this server")
            
            # Send graph
            file = discord.File(buf, filename="mmr_accuracy.png")
            await interaction.followup.send(embed=embed, file=file)
            
        except httpx.HTTPStatusError as e:
            error_msg = f"API error: {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "detail" in error_data:
                    error_msg = error_data["detail"]
            except:
                error_msg = e.response.text
            
            embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to get MMR accuracy data: {error_msg}",
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
                description=f"Failed to generate MMR accuracy graph: {error_msg}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            import traceback
            traceback.print_exc()


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(MMRAccuracyCommand(bot))

