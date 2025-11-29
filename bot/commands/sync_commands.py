"""Command to manually sync Discord commands for troubleshooting."""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio


class SyncCommandsCommand(commands.Cog):
    """Command to manually sync Discord commands (Administrator only)."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="sync-commands", description="Manually sync bot commands to this server (Administrator only)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_commands(self, interaction: discord.Interaction):
        """Manually sync commands to the current guild."""
        if not interaction.guild:
            await interaction.response.send_message(
                "This command can only be used in a server!",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        try:
            guild = interaction.guild
            
            # Clear guild-specific commands
            self.bot.tree.clear_commands(guild=guild)
            await asyncio.sleep(0.5)  # Wait for Discord to process
            
            # Sync global commands to this guild
            synced = await self.bot.tree.sync(guild=guild)
            
            # Get list of command names
            command_names = [cmd.name for cmd in synced]
            
            embed = discord.Embed(
                title="✅ Commands Synced",
                description=f"Successfully synced **{len(synced)}** command(s) to **{guild.name}**",
                color=discord.Color.green()
            )
            
            if command_names:
                embed.add_field(
                    name="Synced Commands",
                    value="\n".join([f"• `/{name}`" for name in sorted(command_names)]),
                    inline=False
                )
            
            embed.add_field(
                name="Note",
                value="Commands may take up to 1 hour to appear globally. This sync forces an immediate update for this server.",
                inline=False
            )
            
            embed.set_footer(text=f"Server ID: {guild.id}")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Also log to console
            print(f"\n[Manual Sync] User {interaction.user} synced commands to '{guild.name}' (ID: {guild.id})", flush=True)
            print(f"[Manual Sync] Synced {len(synced)} command(s): {', '.join(command_names)}", flush=True)
            
        except discord.errors.HTTPException as e:
            error_msg = f"Discord API error: {e.status} - {e.text}"
            if e.code == 50001:  # Missing access
                error_msg = "Bot doesn't have permission to manage commands in this server."
            elif e.code == 50025:  # Invalid form body
                error_msg = "Invalid command structure. Check bot logs for details."
            
            embed = discord.Embed(
                title="❌ Sync Failed",
                description=error_msg,
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            print(f"[Manual Sync] ERROR: {error_msg}", flush=True)
            import traceback
            traceback.print_exc()
            
        except Exception as e:
            error_msg = str(e)
            embed = discord.Embed(
                title="❌ Sync Failed",
                description=f"An error occurred: {error_msg}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            print(f"[Manual Sync] ERROR: {error_msg}", flush=True)
            import traceback
            traceback.print_exc()
    
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Cog-level error handler for app commands."""
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You need **Administrator** permission to use this command.",
                color=discord.Color.red()
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        raise error


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(SyncCommandsCommand(bot))

