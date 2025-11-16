"""Help command for listing available slash commands."""
import discord
from discord import app_commands
from discord.ext import commands


class HelpCommand(commands.Cog):
    """Provide help information about available commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h"])
    async def help_prefix(self, ctx: commands.Context):
        """Prefix command for help - redirects to slash commands."""
        embed = discord.Embed(
            title="📚 League Helper Bot",
            description="This bot uses **slash commands** (/) instead of prefix commands.\n\n"
                       "Type `/` to see all available commands, or use `/help` for a detailed guide!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Quick Commands",
            value="`/connect` - Link your League account\n"
                  "`/generate-teams` - Create balanced teams\n"
                  "`/help` - Full command guide",
            inline=False
        )
        embed.set_footer(text="All commands use the / prefix")
        await ctx.send(embed=embed)

    @app_commands.command(name="help", description="Show available commands and how to use them")
    async def help(self, interaction: discord.Interaction):
        """Send an embed with available commands organized by category."""
        await interaction.response.defer(thinking=True, ephemeral=True)

        # Define command categories with descriptions and examples
        command_categories = {
            "Account Management": {
                "commands": [
                    {
                        "name": "connect",
                        "description": "Connect your League of Legends account to your Discord account",
                        "example": "`/connect game_name:MyUsername tag_line:NA1 tier:Gold rank:III`",
                        "admin": False
                    },
                    {
                        "name": "me",
                        "description": "View your connected League account and current MMR",
                        "example": "`/me`",
                        "admin": False
                    }
                ]
            },
            "Team Generation": {
                "commands": [
                    {
                        "name": "generate-teams",
                        "description": "Generate balanced teams from 10 players (select 10 Discord members)",
                        "example": "`/generate-teams player1:@Player1 player2:@Player2 ...`",
                        "admin": False
                    },
                    {
                        "name": "attendance-check",
                        "description": "Check who's ready to play (attendance check with buttons)",
                        "example": "`/attendance-check`",
                        "admin": False
                    }
                ]
            },
            "Statistics": {
                "commands": [
                    {
                        "name": "leaderboard",
                        "description": "View MMR leaderboard (top players by MMR)",
                        "example": "`/leaderboard limit:20`",
                        "admin": False
                    },
                    {
                        "name": "mmr-history",
                        "description": "View your MMR progression graph over time",
                        "example": "`/mmr-history`",
                        "admin": False
                    }
                ]
            },
            "Administration": {
                "commands": [
                    {
                        "name": "modify-mmr",
                        "description": "Modify a player's MMR (administrator only)",
                        "example": "`/modify-mmr player:@Player new_mmr:1500`",
                        "admin": True
                    },
                    {
                        "name": "guild-id",
                        "description": "Get the current server's (guild) ID",
                        "example": "`/guild-id`",
                        "admin": False
                    }
                ]
            }
        }

        # Build the embed
        embed = discord.Embed(
            title="📚 League Helper Bot - Command Guide",
            description="Here are all available commands organized by category:",
            color=discord.Color.blue()
        )

        # Add each category as a field
        for category_name, category_data in command_categories.items():
            field_value = ""
            for cmd in category_data["commands"]:
                admin_marker = " 🔒" if cmd["admin"] else ""
                field_value += f"**`/{cmd['name']}`**{admin_marker}\n"
                field_value += f"• {cmd['description']}\n"
                field_value += f"• Example: {cmd['example']}\n\n"
            
            embed.add_field(
                name=f"📋 {category_name}",
                value=field_value.strip(),
                inline=False
            )

        # Add footer with additional info
        embed.set_footer(
            text="🔒 = Admin only | Use /help to see this guide again | All commands use slash commands (/)"
        )

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(HelpCommand(bot))


