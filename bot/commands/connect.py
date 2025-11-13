"""Connect command for linking League of Legends accounts."""
import discord
from discord import app_commands
from discord.ext import commands
from bot.utils.api_client import APIClient
import httpx


class ConnectCommand(commands.Cog):
    """Command to connect Discord account to League of Legends account."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_client = APIClient()
    
    @app_commands.command(name="connect", description="Connect your League of Legends account")
    @app_commands.describe(
        game_name="Your League of Legends username (game name)",
        tag_line="Your League of Legends tag line (e.g., NA1, EUW) - NO hashtag needed!",
        tier="Your ranked tier",
        rank="Your rank within tier (I, II, III, IV) - Not needed for Master, Grandmaster, or Challenger"
    )
    @app_commands.choices(tier=[
        app_commands.Choice(name="IRON", value="IRON"),
        app_commands.Choice(name="BRONZE", value="BRONZE"),
        app_commands.Choice(name="SILVER", value="SILVER"),
        app_commands.Choice(name="GOLD", value="GOLD"),
        app_commands.Choice(name="PLATINUM", value="PLATINUM"),
        app_commands.Choice(name="EMERALD", value="EMERALD"),
        app_commands.Choice(name="DIAMOND", value="DIAMOND"),
        app_commands.Choice(name="MASTER", value="MASTER"),
        app_commands.Choice(name="GRANDMASTER", value="GRANDMASTER"),
        app_commands.Choice(name="CHALLENGER", value="CHALLENGER"),
    ])
    @app_commands.choices(rank=[
        app_commands.Choice(name="I", value="I"),
        app_commands.Choice(name="II", value="II"),
        app_commands.Choice(name="III", value="III"),
        app_commands.Choice(name="IV", value="IV"),
    ])
    async def connect(
        self,
        interaction: discord.Interaction,
        game_name: str,
        tag_line: str,
        tier: str,
        rank: str = None
    ):
        """Connect your Discord account to your League of Legends account."""
        print(f"[Bot] /connect command called by {interaction.user} ({interaction.user.id})", flush=True)
        print(f"[Bot] game_name: {game_name}, tag_line: {tag_line}", flush=True)
        
        try:
            print(f"[Bot] About to defer response...", flush=True)
            await interaction.response.defer(thinking=True)
            print(f"[Bot] Response deferred successfully", flush=True)
        except Exception as e:
            print(f"[Bot] ERROR deferring response: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return
        
        try:
            # Call API to connect account
            if not interaction.guild_id:
                await interaction.followup.send("This command can only be used in a server!", ephemeral=True)
                return
            
            print(f"[Bot] Calling API client...", flush=True)
            account = await self.api_client.connect_account(
                str(interaction.user.id),
                interaction.user.display_name,  # Discord display name
                game_name,
                tag_line,
                str(interaction.guild_id),
                highest_tier=tier,
                highest_rank=rank
            )
            print(f"[Bot] Got account from API: {account}")
            
            account_tier = account.get("highest_tier")
            account_rank = account.get("highest_rank")
            
            # Handle None values properly
            if account_tier is None or account_tier == "None":
                tier_display = "Unranked"
            elif account_tier == "UNRANKED":
                tier_display = "Unranked"
            else:
                if account_rank:
                    tier_display = f"{account_tier} {account_rank}"
                else:
                    tier_display = account_tier
            
            embed = discord.Embed(
                title="✅ Account Connected Successfully",
                color=discord.Color.green()
            )
            embed.add_field(name="Riot ID", value=f"{account['game_name']}#{account['tag_line']}", inline=False)
            embed.add_field(name="Current Tier", value=tier_display, inline=True)
            embed.add_field(name="Custom MMR", value=str(account.get('custom_mmr', 1000)), inline=True)
            embed.set_footer(text="Your account has been linked and will be used for team generation!")
            
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
            print(f"[Bot] ERROR in /connect: {error_msg}", flush=True)
            import traceback
            traceback.print_exc()
            
            if "409" in error_msg or "already connected" in error_msg.lower():
                error_msg = "This League account is already connected to another Discord user. Each League account can only be connected to one Discord account."
            elif "duplicate" in error_msg.lower() or "unique constraint" in error_msg.lower():
                error_msg = "This account is already connected. Use `/me` to view your current connection."
            
            embed = discord.Embed(
                title="❌ Connection Failed",
                description=error_msg,
                color=discord.Color.red()
            )
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as followup_error:
                print(f"[Bot] ERROR sending followup: {followup_error}", flush=True)
                # Try to edit the original response if followup fails
                try:
                    await interaction.edit_original_response(content=f"❌ Error: {error_msg}")
                except:
                    pass
    
    @app_commands.command(name="guild-id", description="Get the current server's (guild) ID")
    async def guild_id(self, interaction: discord.Interaction):
        """Display the current server's guild ID."""
        if not interaction.guild_id:
            await interaction.response.send_message("This command can only be used in a server!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🆔 Server ID (Guild ID)",
            description=f"**Guild ID:** `{interaction.guild_id}`\n\n**Server Name:** {interaction.guild.name}",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Use this ID in the migration to replace 'default'")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="me", description="View your connected League of Legends account")
    async def me(self, interaction: discord.Interaction):
        """View your connected League account profile."""
        await interaction.response.defer(thinking=True)
        
        try:
            if not interaction.guild_id:
                await interaction.followup.send("This command can only be used in a server!", ephemeral=True)
                return
            
            # Get user account from API
            account = await self.api_client.get_user_account(str(interaction.user.id), str(interaction.guild_id))
            
            tier = account.get("highest_tier")
            rank = account.get("highest_rank")
            
            # Handle None values properly
            if tier is None or tier == "None":
                tier_display = "Unranked"
            elif tier == "UNRANKED":
                tier_display = "Unranked"
            else:
                if rank:
                    tier_display = f"{tier} {rank}".strip()
                else:
                    tier_display = tier
            
            embed = discord.Embed(
                title="👤 Your League Profile",
                color=discord.Color.blue()
            )
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.add_field(name="Riot ID", value=f"{account['game_name']}#{account['tag_line']}", inline=False)
            embed.add_field(name="Ranked Tier", value=tier_display, inline=True)
            embed.add_field(name="Custom MMR", value=str(account.get('custom_mmr', 1000)), inline=True)
            embed.set_footer(text="Use /connect to update your account")
            
            await interaction.followup.send(embed=embed)
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                embed = discord.Embed(
                    title="❌ No Account Connected",
                    description="You haven't connected a League of Legends account yet.\n\nUse `/connect` to link your account!",
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
                description=f"Failed to fetch your profile: {error_msg}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(ConnectCommand(bot))

