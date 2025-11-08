"""인원췤 (Headcount check) command."""
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime, timedelta
from typing import Set


class AttendanceView(View):
    """View with buttons for checking attendance."""
    
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
        self.ready_players: Set[int] = set()  # Set of user IDs who are ready
    
    def update_embed(self) -> discord.Embed:
        """Create updated embed with current player list."""
        embed = discord.Embed(
            title="🎮 인원췤 - Player Check",
            description="Click the button below if you're ready to play today!",
            color=discord.Color.blue()
        )
        
        if self.ready_players:
            # Show list of ready players
            player_list = "\n".join([f"<@{user_id}>" for user_id in self.ready_players])
            embed.add_field(
                name=f"✅ Ready to Play ({len(self.ready_players)} players)",
                value=player_list,
                inline=False
            )
        else:
            embed.add_field(
                name="✅ Ready to Play (0 players)",
                value="*No one yet... be the first!*",
                inline=False
            )
        
        embed.set_footer(text=f"Last updated: {datetime.now().strftime('%I:%M %p')}")
        
        return embed
    
    @discord.ui.button(label="I'm Ready! 🎮", style=discord.ButtonStyle.success, custom_id="attendance_join")
    async def join_button(self, interaction: discord.Interaction, button: Button):
        """Handle when someone clicks 'I'm Ready'."""
        user_id = interaction.user.id
        
        if user_id in self.ready_players:
            await interaction.response.send_message(
                "You're already on the list! 🎮",
                ephemeral=True
            )
            return
        
        # Add player to ready list
        self.ready_players.add(user_id)
        
        # Update the message
        embed = self.update_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Send confirmation to user
        await interaction.followup.send(
            f"✅ Added you to the player list! ({len(self.ready_players)}/10)",
            ephemeral=True
        )
    
    @discord.ui.button(label="Can't Play ❌", style=discord.ButtonStyle.danger, custom_id="attendance_leave")
    async def leave_button(self, interaction: discord.Interaction, button: Button):
        """Handle when someone clicks 'Can't Play'."""
        user_id = interaction.user.id
        
        if user_id not in self.ready_players:
            await interaction.response.send_message(
                "You're not on the list!",
                ephemeral=True
            )
            return
        
        # Remove player from ready list
        self.ready_players.remove(user_id)
        
        # Update the message
        embed = self.update_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Send confirmation to user
        await interaction.followup.send(
            "❌ Removed you from the player list.",
            ephemeral=True
        )
    
    @discord.ui.button(label="Clear List 🔄", style=discord.ButtonStyle.secondary, custom_id="attendance_clear")
    async def clear_button(self, interaction: discord.Interaction, button: Button):
        """Handle clearing the list (admin only)."""
        # Check if user has manage messages permission
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "❌ Only moderators can clear the list!",
                ephemeral=True
            )
            return
        
        # Clear the list
        self.ready_players.clear()
        
        # Update the message
        embed = self.update_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Send confirmation
        await interaction.followup.send(
            "🔄 Player list has been cleared!",
            ephemeral=True
        )


class AttendanceCommand(commands.Cog):
    """Command for checking who's ready to play."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="인원췤", description="Check who's ready to play today")
    async def attendance_check(self, interaction: discord.Interaction):
        """Create a player availability check."""
        view = AttendanceView()
        embed = view.update_embed()
        
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(AttendanceCommand(bot))

