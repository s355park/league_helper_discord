"""Modify MMR command for administrators."""
import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.api_client import APIClient
import httpx


class ModifyMMRCommand(commands.Cog):
    """Command to modify a player's MMR (administrator only)."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_client = APIClient()
    
    @app_commands.command(name="modify-mmr", description="Modify a player's MMR (Administrator only)")
    @app_commands.describe(
        player="The player whose MMR you want to modify",
        new_mmr="The new MMR value (must be a positive integer)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def modify_mmr(
        self,
        interaction: discord.Interaction,
        player: discord.Member,
        new_mmr: int
    ):
        """Modify a player's MMR (administrator only)."""
        await interaction.response.defer(thinking=True)
        
        if not interaction.guild_id:
            await interaction.followup.send("This command can only be used in a server!", ephemeral=True)
            return
        
        # Validate MMR value
        if new_mmr < 0:
            embed = discord.Embed(
                title="❌ Invalid MMR Value",
                description="MMR must be a positive integer (0 or greater).",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        try:
            # Get current MMR
            discord_id = str(player.id)
            account = await self.api_client.get_user_account(discord_id, str(interaction.guild_id))
            old_mmr = account.get("custom_mmr", 1000)
            
            # Update MMR via API
            result = await self.api_client.modify_player_mmr(
                discord_id,
                new_mmr,
                str(interaction.guild_id)
            )
            
            # Create success embed
            embed = discord.Embed(
                title="✅ MMR Modified Successfully",
                description=f"**{player.display_name}**'s MMR has been updated.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Old MMR",
                value=f"{old_mmr}",
                inline=True
            )
            embed.add_field(
                name="New MMR",
                value=f"{new_mmr}",
                inline=True
            )
            embed.add_field(
                name="Change",
                value=f"{'+' if new_mmr >= old_mmr else ''}{new_mmr - old_mmr}",
                inline=True
            )
            embed.set_footer(text=f"Modified by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                embed = discord.Embed(
                    title="❌ Account Not Found",
                    description=f"**{player.display_name}** has not connected their League account yet.\n\nThey need to use `/connect` first.",
                    color=discord.Color.orange()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                error_msg = f"API error: {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    error_msg = e.response.text
                
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to modify MMR: {error_msg}",
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
                description=f"Failed to modify MMR: {error_msg}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            import traceback
            traceback.print_exc()


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(ModifyMMRCommand(bot))

