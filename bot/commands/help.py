"""Help command for listing available slash commands."""
import discord
from discord import app_commands
from discord.ext import commands


class HelpCommand(commands.Cog):
    """Provide help information about available commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show available commands and how to use them")
    async def help(self, interaction: discord.Interaction):
        """Send an embed with available commands."""
        await interaction.response.defer(thinking=True, ephemeral=True)

        commands_list = []
        for cmd in self.bot.tree.get_commands():
            # Skip context menu commands; focus on chat input commands
            if not isinstance(cmd, app_commands.Command):
                continue
            # Skip hidden/internal commands if any
            if getattr(cmd, "hidden", False):
                continue

            is_admin_only = False
            # Detect admin-only via default_permissions or checks metadata
            try:
                default_perms = getattr(cmd, "default_permissions", None)
                if default_perms and getattr(default_perms, "administrator", False):
                    is_admin_only = True
            except Exception:
                pass
            # Fallback: mark known admin commands
            if cmd.name in {"modify-mmr"}:
                is_admin_only = True

            marker = " (admin)" if is_admin_only else ""
            desc = (cmd.description or "").strip()
            commands_list.append((cmd.name, desc, marker))

        # Sort alphabetically
        commands_list.sort(key=lambda x: x[0])

        embed = discord.Embed(
            title="Help",
            description="Slash commands available in this bot.",
            color=discord.Color.blurple(),
        )

        # Build lines compactly
        lines = []
        for name, desc, marker in commands_list:
            display_desc = desc if desc else "No description provided."
            lines.append(f"/{name}{marker} — {display_desc}")

        # Discord embed field length constraints; chunk if necessary
        chunk = []
        chunk_len = 0
        max_field_len = 1024
        fields = []
        for line in lines:
            line_len = len(line) + 1
            if chunk_len + line_len > max_field_len:
                fields.append("\n".join(chunk))
                chunk = [line]
                chunk_len = line_len
            else:
                chunk.append(line)
                chunk_len += line_len
        if chunk:
            fields.append("\n".join(chunk))

        if not fields:
            fields = ["No commands found."]

        # Add fields to embed
        for i, field_text in enumerate(fields, start=1):
            embed.add_field(name=f"Commands {i}", value=field_text, inline=False)

        embed.set_footer(text="Admin-only commands are marked with (admin)")

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Setup function for the cog."""
    await bot.add_cog(HelpCommand(bot))


