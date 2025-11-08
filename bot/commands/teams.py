"""Generate teams command."""
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
from bot.utils.api_client import APIClient
from typing import List


class MatchResultView(View):
    """View with buttons for recording match results."""
    
    def __init__(self, match_id: str, team1_ids: List[str], team2_ids: List[str], api_client: APIClient):
        super().__init__(timeout=3600)  # 1 hour timeout
        self.match_id = match_id
        self.team1_ids = team1_ids
        self.team2_ids = team2_ids
        self.api_client = api_client
        self.result_recorded = False
    
    @discord.ui.button(label="Team 1 Won 🔵", style=discord.ButtonStyle.primary, custom_id="team1_won")
    async def team1_won(self, interaction: discord.Interaction, button: Button):
        """Handle Team 1 win button."""
        if self.result_recorded:
            await interaction.response.send_message("Match result already recorded!", ephemeral=True)
            return
        
        await interaction.response.defer(thinking=True)
        
        try:
            result = await self.api_client.record_match_result(
                self.match_id,
                1,
                self.team1_ids,
                self.team2_ids
            )
            
            self.result_recorded = True
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.message.edit(view=self)
            
            embed = discord.Embed(
                title="✅ Match Result Recorded",
                description=result["message"],
                color=discord.Color.green()
            )
            
            # Show MMR changes
            mmr_text = ""
            for discord_id in self.team1_ids:
                change = result["mmr_changes"].get(discord_id, 0)
                mmr_text += f"<@{discord_id}>: **+{change}** MMR\n"
            
            mmr_text += "\n"
            for discord_id in self.team2_ids:
                change = result["mmr_changes"].get(discord_id, 0)
                mmr_text += f"<@{discord_id}>: **{change}** MMR\n"
            
            embed.add_field(name="MMR Changes", value=mmr_text, inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error Recording Result",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Team 2 Won 🔴", style=discord.ButtonStyle.danger, custom_id="team2_won")
    async def team2_won(self, interaction: discord.Interaction, button: Button):
        """Handle Team 2 win button."""
        if self.result_recorded:
            await interaction.response.send_message("Match result already recorded!", ephemeral=True)
            return
        
        await interaction.response.defer(thinking=True)
        
        try:
            result = await self.api_client.record_match_result(
                self.match_id,
                2,
                self.team1_ids,
                self.team2_ids
            )
            
            self.result_recorded = True
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.message.edit(view=self)
            
            embed = discord.Embed(
                title="✅ Match Result Recorded",
                description=result["message"],
                color=discord.Color.green()
            )
            
            # Show MMR changes
            mmr_text = ""
            for discord_id in self.team1_ids:
                change = result["mmr_changes"].get(discord_id, 0)
                mmr_text += f"<@{discord_id}>: **{change}** MMR\n"
            
            mmr_text += "\n"
            for discord_id in self.team2_ids:
                change = result["mmr_changes"].get(discord_id, 0)
                mmr_text += f"<@{discord_id}>: **{change}** MMR\n"
            
            embed.add_field(name="MMR Changes", value=mmr_text, inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error Recording Result",
                description=str(e),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Cancel ❌", style=discord.ButtonStyle.secondary, custom_id="cancel")
    async def cancel(self, interaction: discord.Interaction, button: Button):
        """Handle cancel button."""
        if self.result_recorded:
            await interaction.response.send_message("Match result already recorded!", ephemeral=True)
            return
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("Match result cancelled. No MMR changes recorded.", ephemeral=True)


class TeamsCommand(commands.Cog):
    """Command to generate balanced teams."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_client = APIClient()
    
    @app_commands.command(name="generate-teams", description="Generate balanced teams from 10 players")
    @app_commands.describe(
        player1="First player",
        player2="Second player",
        player3="Third player",
        player4="Fourth player",
        player5="Fifth player",
        player6="Sixth player",
        player7="Seventh player",
        player8="Eighth player",
        player9="Ninth player",
        player10="Tenth player"
    )
    async def generate_teams(
        self,
        interaction: discord.Interaction,
        player1: discord.Member,
        player2: discord.Member,
        player3: discord.Member,
        player4: discord.Member,
        player5: discord.Member,
        player6: discord.Member,
        player7: discord.Member,
        player8: discord.Member,
        player9: discord.Member,
        player10: discord.Member
    ):
        """Generate balanced teams from 10 Discord users."""
        await interaction.response.defer(thinking=True)
        
        # Collect Discord IDs
        players = [
            player1, player2, player3, player4, player5,
            player6, player7, player8, player9, player10
        ]
        
        discord_ids = [str(p.id) for p in players]
        
        # Check for duplicates
        if len(set(discord_ids)) != 10:
            embed = discord.Embed(
                title="❌ Error",
                description="All 10 players must be unique!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        try:
            # Call API to generate teams
            result = await self.api_client.generate_teams(discord_ids)
            
            team1 = result["team1"]
            team2 = result["team2"]
            tier_difference = result["tier_difference"]
            match_id = result.get("match_id", "")
            
            # Build team display
            team1_text = self._format_team(team1, players)
            team2_text = self._format_team(team2, players)
            
            # Get team player IDs
            team1_ids = [str(p["discord_id"]) for p in team1["players"]]
            team2_ids = [str(p["discord_id"]) for p in team2["players"]]
            
            embed = discord.Embed(
                title="⚔️ Balanced Teams Generated",
                color=discord.Color.blue()
            )
            embed.add_field(
                name=f"🔵 Team 1 (Total MMR: {team1['total_tier_value']})",
                value=team1_text,
                inline=False
            )
            embed.add_field(
                name=f"🔴 Team 2 (Total MMR: {team2['total_tier_value']})",
                value=team2_text,
                inline=False
            )
            embed.add_field(
                name="Balance",
                value=f"MMR difference: {tier_difference}",
                inline=False
            )
            embed.set_footer(text="Teams are balanced based on custom MMR! Click a button after the match to update MMR.")
            
            # Create view with buttons
            view = MatchResultView(match_id, team1_ids, team2_ids, self.api_client)
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            error_msg = str(e)
            if "not connected" in error_msg.lower():
                error_msg = "Some players have not connected their League accounts. Please use /connect first."
            elif "400" in error_msg:
                error_msg = "Invalid request. Please ensure all 10 players are valid."
            
            embed = discord.Embed(
                title="❌ Team Generation Failed",
                description=error_msg,
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="generate-teams-voice", description="Generate balanced teams from players in your voice channel")
    async def generate_teams_voice(self, interaction: discord.Interaction):
        """Generate balanced teams from members in the voice channel."""
        await interaction.response.defer(thinking=True)
        
        # Check if user is in a voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = discord.Embed(
                title="❌ Not in Voice Channel",
                description="You must be in a voice channel to use this command!",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        voice_channel = interaction.user.voice.channel
        
        # Get all members in the voice channel (excluding bots)
        members = [member for member in voice_channel.members if not member.bot]
        
        # Check if there are exactly 10 people
        if len(members) < 10:
            embed = discord.Embed(
                title="❌ Not Enough Players",
                description=f"Found {len(members)} player(s) in the voice channel.\n\nYou need exactly **10 players** to generate teams!",
                color=discord.Color.red()
            )
            if len(members) > 0:
                member_list = ", ".join([m.display_name for m in members[:5]])
                if len(members) > 5:
                    member_list += f", ... (+{len(members) - 5} more)"
                embed.add_field(name="Players in channel", value=member_list, inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        if len(members) > 10:
            embed = discord.Embed(
                title="❌ Too Many Players",
                description=f"Found {len(members)} player(s) in the voice channel.\n\nYou need exactly **10 players** to generate teams!\n\nUse `/generate-teams` to manually select 10 players.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Collect Discord IDs
        discord_ids = [str(member.id) for member in members]
        
        try:
            # Call API to generate teams
            result = await self.api_client.generate_teams(discord_ids)
            
            team1 = result["team1"]
            team2 = result["team2"]
            tier_difference = result["tier_difference"]
            match_id = result.get("match_id", "")
            
            # Build team display
            team1_text = self._format_team(team1, members)
            team2_text = self._format_team(team2, members)
            
            # Get team player IDs
            team1_ids = [str(p["discord_id"]) for p in team1["players"]]
            team2_ids = [str(p["discord_id"]) for p in team2["players"]]
            
            embed = discord.Embed(
                title="⚔️ Balanced Teams Generated",
                description=f"From voice channel: **{voice_channel.name}**",
                color=discord.Color.blue()
            )
            embed.add_field(
                name=f"🔵 Team 1 (Total MMR: {team1['total_tier_value']})",
                value=team1_text,
                inline=False
            )
            embed.add_field(
                name=f"🔴 Team 2 (Total MMR: {team2['total_tier_value']})",
                value=team2_text,
                inline=False
            )
            embed.add_field(
                name="Balance",
                value=f"MMR difference: {tier_difference}",
                inline=False
            )
            embed.set_footer(text="Teams are balanced based on custom MMR! Click a button after the match to update MMR.")
            
            # Create view with buttons
            view = MatchResultView(match_id, team1_ids, team2_ids, self.api_client)
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            error_msg = str(e)
            if "not connected" in error_msg.lower():
                error_msg = "Some players in the voice channel have not connected their League accounts. Please use /connect first."
            elif "400" in error_msg:
                error_msg = "Invalid request. Please ensure all players in the voice channel have connected accounts."
            
            embed = discord.Embed(
                title="❌ Team Generation Failed",
                description=error_msg,
                color=discord.Color.red()
            )
            embed.add_field(
                name="Voice Channel",
                value=f"{voice_channel.mention} ({len(members)} players)",
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    def _format_team(self, team_data: dict, all_players: List[discord.Member]) -> str:
        """Format team data for display."""
        lines = []
        player_map = {str(p.id): p for p in all_players}
        
        for player_info in team_data["players"]:
            discord_id = player_info["discord_id"]
            member = player_map.get(discord_id)
            
            if member:
                display_name = member.mention
            else:
                display_name = player_info["game_name"]
            
            tier = player_info.get("highest_tier", "UNRANKED")
            rank = player_info.get("highest_rank", "")
            tier_display = f"{tier} {rank}".strip() if tier != "UNRANKED" else "Unranked"
            
            lines.append(f"{display_name} - {tier_display}")
        
        return "\n".join(lines) if lines else "No players"


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(TeamsCommand(bot))

