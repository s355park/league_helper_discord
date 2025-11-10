"""MMR history command with graph visualization."""
import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.api_client import APIClient
import httpx
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import io
from typing import Optional


class MMRHistoryCommand(commands.Cog):
    """Command to view MMR history graph."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_client = APIClient()
    
    @app_commands.command(name="mmr-history", description="View your MMR progression over time")
    async def mmr_history(self, interaction: discord.Interaction):
        """Display MMR history graph."""
        await interaction.response.defer(thinking=True)
        
        if not interaction.guild_id:
            await interaction.followup.send("This command can only be used in a server!", ephemeral=True)
            return
        
        try:
            # Get match history from API
            discord_id = str(interaction.user.id)
            url = f"{self.api_client.base_url}/users/{discord_id}/match-history"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params={"guild_id": str(interaction.guild_id)}, timeout=10.0)
                response.raise_for_status()
                data = response.json()
            
            matches = data.get("matches", [])
            
            if not matches:
                embed = discord.Embed(
                    title="📊 MMR History",
                    description="You haven't played any matches yet!\n\nPlay some games and record results to see your MMR progression.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Get current MMR
            print(f"[Bot] Getting user account for MMR history...", flush=True)
            account = await self.api_client.get_user_account(discord_id, str(interaction.guild_id))
            current_mmr = account.get("custom_mmr", 1000)
            print(f"[Bot] Current MMR: {current_mmr}", flush=True)
            
            # Prepare data for graph
            # Reverse matches to show chronological order (oldest to newest)
            matches.reverse()
            
            # Build MMR progression
            mmr_values = []
            match_numbers = []
            annotations = []  # For win/loss markers
            
            # Start with initial MMR (first match's MMR before change)
            if matches[0].get("mmr_at_match"):
                current = matches[0]["mmr_at_match"]
            else:
                # If no MMR stored, estimate backwards from current
                current = current_mmr
                for match in reversed(matches):
                    current -= match.get("mmr_change", 0)
            
            # Add starting point (before first match)
            match_numbers.append(0)
            mmr_values.append(current)
            annotations.append(None)
            
            # Process each match
            for match_num, match in enumerate(matches, start=1):
                mmr_change = match.get("mmr_change", 0)
                won = match.get("won", False)
                
                # Add point after match
                current += mmr_change
                
                match_numbers.append(match_num)
                mmr_values.append(current)
                annotations.append("W" if won else "L")
            
            if not match_numbers:
                embed = discord.Embed(
                    title="❌ Error",
                    description="No match data available.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Create graph
            print(f"[Bot] Creating matplotlib graph...", flush=True)
            try:
                fig, ax = plt.subplots(figsize=(12, 6))
            except Exception as e:
                print(f"[Bot] ERROR creating matplotlib figure: {e}", flush=True)
                raise
            ax.plot(match_numbers, mmr_values, linewidth=2, color='#5865F2', marker='o', markersize=6)
            
            # Add win/loss markers
            for i, (match_num, mmr, annotation) in enumerate(zip(match_numbers, mmr_values, annotations)):
                if annotation:
                    color = '#57F287' if annotation == "W" else '#ED4245'
                    ax.scatter(match_num, mmr, color=color, s=120, zorder=5, alpha=0.8, edgecolors='white', linewidths=1)
            
            # Formatting
            ax.set_xlabel('Match #', fontsize=11, color='white')
            ax.set_ylabel('MMR', fontsize=11, color='white')
            ax.set_title(f'{interaction.user.display_name}\'s MMR Progression', 
                        fontsize=14, fontweight='bold', color='white', pad=20)
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # Set x-axis to show match numbers as integers
            ax.set_xticks(match_numbers)
            ax.set_xticklabels([str(m) if m > 0 else "Start" for m in match_numbers])
            
            # Set dark theme
            fig.patch.set_facecolor('#2F3136')
            ax.set_facecolor('#36393F')
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            
            # Add current MMR text
            if mmr_values:
                final_mmr = mmr_values[-1]
                ax.text(0.02, 0.98, f'Current MMR: {final_mmr}', 
                       transform=ax.transAxes, fontsize=10, 
                       verticalalignment='top', color='white',
                       bbox=dict(boxstyle='round', facecolor='#2F3136', alpha=0.8))
            
            # Add legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='#57F287', label='Win'),
                Patch(facecolor='#ED4245', label='Loss')
            ]
            ax.legend(handles=legend_elements, loc='upper left', facecolor='#2F3136', edgecolor='white', labelcolor='white')
            
            plt.tight_layout()
            
            # Save to bytes
            print(f"[Bot] Saving graph to bytes...", flush=True)
            buf = io.BytesIO()
            try:
                plt.savefig(buf, format='png', facecolor='#2F3136', dpi=100, bbox_inches='tight')
                buf.seek(0)
                plt.close()
                print(f"[Bot] Graph saved successfully, size: {len(buf.getvalue())} bytes", flush=True)
            except Exception as e:
                plt.close()
                print(f"[Bot] ERROR saving graph: {e}", flush=True)
                raise
            
            # Create embed
            print(f"[Bot] Creating embed and sending response...", flush=True)
            embed = discord.Embed(
                title="📊 MMR History",
                description=f"Your MMR progression over {len(matches)} match(es)",
                color=discord.Color.blue()
            )
            embed.set_image(url="attachment://mmr_history.png")
            embed.set_footer(text=f"Current MMR: {current_mmr}")
            
            # Send graph
            file = discord.File(buf, filename="mmr_history.png")
            await interaction.followup.send(embed=embed, file=file)
            print(f"[Bot] MMR history sent successfully!", flush=True)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                embed = discord.Embed(
                    title="❌ No Account Connected",
                    description="You haven't connected your League account yet.\n\nUse `/connect` to link your account!",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                raise
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
                description=f"Failed to generate MMR history: {error_msg}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            import traceback
            traceback.print_exc()


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(MMRHistoryCommand(bot))

