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
            
            # Prepare data for graph
            match_numbers = [dp["match_number"] for dp in data_points]
            win_rates = [dp["cumulative_win_rate"] for dp in data_points]
            
            # Create graph
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Plot the win rate line
            ax.plot(match_numbers, win_rates, linewidth=2, color='#5865F2', marker='o', markersize=4, alpha=0.7)
            
            # Add a horizontal line at 50% (expected if MMR is perfectly balanced)
            ax.axhline(y=50, color='#ED4245', linestyle='--', linewidth=1.5, alpha=0.5, label='50% (Perfect Balance)')
            
            # Add a horizontal line at overall win rate
            ax.axhline(y=overall_win_rate, color='#57F287', linestyle='--', linewidth=1.5, alpha=0.5, label=f'Overall: {overall_win_rate:.1f}%')
            
            # Formatting
            ax.set_xlabel('Match #', fontsize=11, color='white')
            ax.set_ylabel('Win Rate (%)', fontsize=11, color='white')
            ax.set_title('MMR Accuracy: Higher MMR Team Win Rate Over Time', 
                        fontsize=14, fontweight='bold', color='white', pad=20)
            ax.set_ylim(0, 100)
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # Set dark theme
            fig.patch.set_facecolor('#2F3136')
            ax.set_facecolor('#36393F')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            
            # Add legend
            ax.legend(loc='best', facecolor='#2F3136', edgecolor='white', labelcolor='white')
            
            # Add statistics text
            stats_text = f'Matches Analyzed: {matches_analyzed}\nOverall Win Rate: {overall_win_rate:.1f}%'
            ax.text(0.02, 0.98, stats_text, 
                   transform=ax.transAxes, fontsize=10, 
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

