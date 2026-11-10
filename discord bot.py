"""import discord 
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")
from dotenv import dotenv_values
env_path = Path(__file__).parent / ".env"
print("size in bytes:", env_path.stat().st_size)
print("keys found:", [repr(k) for k in dotenv_values(env_path).keys()])
print(".env exists:", (Path(__file__).parent / ".env").exists())

token = os.getenv("DISCORD_TOKEN")
guild_id = int(os.getenv("GUILD_ID"))

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

GUILD = discord.Object(id=guild_id)

@bot.event
async def setup_hook():
    bot.tree.copy_global_to(guild=GUILD)
    await bot.tree.sync(guild=GUILD)

@bot.event
async def on_ready():
    print("hello")


@bot.tree.command(name="createteam", description="create a private team")
async def createteam(
    interaction: discord.Interaction,
    teamname: str,
    member1: discord.Member,
    member2: discord.Member = None,
    member3: discord.Member = None,
):
    await interaction.response.defer()

    # collect members, add the person who ran the command, remove duplicates
    members = [interaction.user, member1, member2, member3]
    members = list({m.id: m for m in members if m is not None}.values())

    guild = interaction.guild

    # hidden from everyone, visible to the team
    overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
    for m in members:
        overwrites[m] = discord.PermissionOverwrite(view_channel=True, connect=True)

    category = await guild.create_category(teamname, overwrites=overwrites)
    await guild.create_text_channel("text", category=category, overwrites=overwrites)
    await guild.create_voice_channel("voice", category=category, overwrites=overwrites)

    names = ", ".join(m.mention for m in members)
    await interaction.followup.send(f"Created team **{teamname}** with {names}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)"""

import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")
token = os.getenv("DISCORD_TOKEN")
guild_id = int(os.getenv("GUILD_ID"))

# Set up logging
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Prefix is technically required, but we are using Slash Commands.
bot = commands.Bot(command_prefix="!", intents=intents)

GUILD = discord.Object(id=guild_id)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        # Sync slash commands to your specific server so they appear instantly
        bot.tree.copy_global_to(guild=GUILD)
        await bot.tree.sync(guild=GUILD)
        print("Slash commands synced!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="createteam", description="Create a private team")
async def createteam(
    interaction: discord.Interaction,
    teamname: str,
    member1: discord.Member,
    member2: discord.Member = None,
    member3: discord.Member = None,
):
    # Tell Discord we received the command (gives us 15 minutes to process)
    await interaction.response.defer()

    # Collect members, add the person who ran the command, remove duplicates
    members = [interaction.user, member1, member2, member3]
    members = list({m.id: m for m in members if m is not None}.values())

    guild = interaction.guild

    # Set up permissions
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False), # Hide from @everyone
        guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True) # ALLOW THE BOT
    }
    
    # Allow the specific team members
    for m in members:
        overwrites[m] = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True, send_messages=True)

    try:
        # Create the category and channels
        category = await guild.create_category(teamname, overwrites=overwrites)
        text_channel = await guild.create_text_channel("text", category=category, overwrites=overwrites)
        voice_channel = await guild.create_voice_channel("voice", category=category, overwrites=overwrites)

        names = ", ".join(m.mention for m in members)
        
        # Send confirmation in the original channel
        await interaction.followup.send(f"Created team **{teamname}**  Go to {text_channel.mention}!")
        
        # Send a welcome message inside the new private text channel
        await text_channel.send(f"Welcome to team **{teamname}**! {names}")

    except discord.Forbidden:
        await interaction.followup.send("Error: I don't have permission to create channels. Check my role permissions.")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)