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
            
            if matches_analyzed == 0:
                embed = discord.Embed(
                    title="📊 MMR Analysis",
                    description="No matches found to analyze!\n\nPlay some games and record results to see MMR analysis.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            stabilization_data = data.get("stabilization_data", [])
            calibration_data = data.get("calibration_data", [])
            avg_change_first = data.get("avg_mmr_change_first_half", 0)
            avg_change_second = data.get("avg_mmr_change_second_half", 0)
            overall_accuracy = data.get("overall_accuracy", 0.0)
            recent_accuracy = data.get("recent_accuracy", 0.0)
            recent_matches_count = data.get("recent_matches_count", 0)
            
            # Create a figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
            
            # Subplot 1: MMR Change Magnitude Over Time (Stabilization)
            if stabilization_data:
                match_numbers = [dp["match_number"] for dp in stabilization_data]
                mmr_changes = [dp["mmr_change_magnitude"] for dp in stabilization_data]
                
                ax1.plot(match_numbers, mmr_changes, linewidth=2, color='#5865F2', marker='o', markersize=3, alpha=0.6, label='MMR Change')
                
                # Add average lines
                if len(match_numbers) > 1:
                    mid_point = len(match_numbers) // 2
                    ax1.axvline(x=mid_point, color='#ED4245', linestyle='--', linewidth=1, alpha=0.5)
                    ax1.axhline(y=avg_change_first, color='#57F287', linestyle='--', linewidth=1.5, alpha=0.7, label=f'First Half Avg: {avg_change_first:.1f}')
                    ax1.axhline(y=avg_change_second, color='#FEE75C', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Second Half Avg: {avg_change_second:.1f}')
                
                ax1.set_xlabel('Match #', fontsize=11, color='white')
                ax1.set_ylabel('MMR Change Magnitude', fontsize=11, color='white')
                ax1.set_title('MMR Stabilization Over Time', fontsize=13, fontweight='bold', color='white', pad=15)
                ax1.grid(True, alpha=0.3, linestyle='--')
                ax1.legend(loc='best', facecolor='#2F3136', edgecolor='white', labelcolor='white', fontsize=9)
            
            # Subplot 2: Calibration (Expected vs Actual Win Rate)
            if calibration_data:
                ranges = [cd["mmr_difference_range"] for cd in calibration_data]
                expected = [cd["expected_win_rate"] for cd in calibration_data]
                actual = [cd["actual_win_rate"] for cd in calibration_data]
                matches_count = [cd["matches"] for cd in calibration_data]
                
                x_pos = range(len(ranges))
                width = 0.35
                
                bars1 = ax2.bar([x - width/2 for x in x_pos], expected, width, label='Expected', color='#57F287', alpha=0.7)
                bars2 = ax2.bar([x + width/2 for x in x_pos], actual, width, label='Actual', color='#5865F2', alpha=0.7)
                
                # Add match count labels on bars
                for i, (bar1, bar2, count) in enumerate(zip(bars1, bars2, matches_count)):
                    height1 = bar1.get_height()
                    height2 = bar2.get_height()
                    ax2.text(bar1.get_x() + bar1.get_width()/2., height1 + 1, f'n={count}', 
                            ha='center', va='bottom', color='white', fontsize=8)
                
                ax2.set_xlabel('MMR Difference Range', fontsize=11, color='white')
                ax2.set_ylabel('Win Rate (%)', fontsize=11, color='white')
                ax2.set_title('MMR Calibration: Expected vs Actual', fontsize=13, fontweight='bold', color='white', pad=15)
                ax2.set_xticks(x_pos)
                ax2.set_xticklabels(ranges, color='white')
                ax2.set_ylim(0, 100)
                ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
                ax2.legend(loc='best', facecolor='#2F3136', edgecolor='white', labelcolor='white')
            
            # Set dark theme for both subplots
            fig.patch.set_facecolor('#2F3136')
            for ax in [ax1, ax2]:
                ax.set_facecolor('#36393F')
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['right'].set_color('white')
                ax.spines['left'].set_color('white')
            
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
            
            # Create embed with comprehensive analysis
            embed = discord.Embed(
                title="📊 MMR Stability & Accuracy Analysis",
                description=f"Analyzed **{matches_analyzed}** matches in this server",
                color=discord.Color.blue()
            )
            
            # Stabilization analysis
            stabilization_status = ""
            if avg_change_second < avg_change_first * 0.8:
                stabilization_status = "✅ **MMR is stabilizing!** Average change decreased by {:.1f}%".format(
                    (1 - avg_change_second/avg_change_first) * 100 if avg_change_first > 0 else 0
                )
            elif avg_change_second > avg_change_first * 1.2:
                stabilization_status = "⚠️ **MMR changes are increasing.** Average change increased by {:.1f}%".format(
                    ((avg_change_second/avg_change_first) - 1) * 100 if avg_change_first > 0 else 0
                )
            else:
                stabilization_status = "➡️ **MMR changes are stable.** Average change: {:.1f} → {:.1f}".format(
                    avg_change_first, avg_change_second
                )
            
            embed.add_field(
                name="📉 Stabilization",
                value=f"{stabilization_status}\n*Lower MMR changes over time indicate stabilization*",
                inline=False
            )
            
            # Accuracy analysis
            accuracy_status = ""
            if overall_accuracy > 60:
                accuracy_status = "✅ **Excellent accuracy!** MMR strongly predicts winners."
            elif overall_accuracy > 50:
                accuracy_status = "✅ **Good accuracy.** MMR reasonably predicts winners."
            elif overall_accuracy > 40:
                accuracy_status = "⚠️ **Moderate accuracy.** MMR prediction is weak."
            else:
                accuracy_status = "❌ **Low accuracy.** MMR may not reflect skill well."
            
            embed.add_field(
                name="🎯 Prediction Accuracy",
                value=f"{accuracy_status}\n**Overall:** {overall_accuracy:.1f}%\n**Recent ({recent_matches_count} matches):** {recent_accuracy:.1f}%",
                inline=False
            )
            
            # Calibration summary
            if calibration_data:
                calibration_text = ""
                for cd in calibration_data:
                    diff = cd["difference"]
                    if abs(diff) < 5:
                        status = "✅"
                    elif abs(diff) < 10:
                        status = "⚠️"
                    else:
                        status = "❌"
                    calibration_text += f"{status} {cd['mmr_difference_range']}: {cd['actual_win_rate']:.1f}% (expected {cd['expected_win_rate']:.1f}%)\n"
                
                embed.add_field(
                    name="⚖️ Calibration by MMR Difference",
                    value=calibration_text or "Not enough data",
                    inline=False
                )
            
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

