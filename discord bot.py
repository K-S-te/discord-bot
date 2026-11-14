import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from pathlib import Path


load_dotenv(Path(__file__).parent / ".env")
token = os.getenv("DISCORD_TOKEN")
guild_id = int(os.getenv("GUILD_ID"))


handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

          
bot = commands.Bot(command_prefix="/", intents=intents)

GUILD = discord.Object(id=guild_id)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:

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
    if (member1.id == interaction.user.id or 
       (member2 and member2.id==interaction.user.id) or 
       (member3 and member3.id==interaction.user.id)):
        await interaction.response.send_message(
            content="You can't list your name as member, you are automatically added to the team",
            ephemeral=True
        )
        return

    if ((member2 and member1.id == member2.id) or 
        (member3 and member1.id == member3.id) or 
        (member2 and member3 and member2.id ==  member3.id)):
            await interaction.response.send_message(
                content="You can't list a member more then once",
                ephemeral=True
            )
            return
    
    await interaction.response.defer()

 
    members = [interaction.user, member1, member2, member3]
    members = list({m.id: m for m in members if m is not None}.values())

    guild = interaction.guild

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False), 
        guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)
    }
    

    for m in members:
        overwrites[m] = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True, send_messages=True)

    try:

        category = await guild.create_category(teamname, overwrites=overwrites)
        text_channel = await guild.create_text_channel("text", category=category, overwrites=overwrites)
        voice_channel = await guild.create_voice_channel("voice", category=category, overwrites=overwrites)

        names = ", ".join(m.mention for m in members)

        await interaction.followup.send(f"Created team **{teamname}**  Go to {text_channel.mention}!")
        
        await text_channel.send(f"Welcome to team **{teamname}**! {names}")

    except discord.Forbidden:
        await interaction.followup.send("Error: I don't have permission to create channels. Check my role permissions.")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

@bot.tree.command(name="addmember", description="Add a member to an already existing team")
async def addmember(
    interaction: discord.Interaction,
    teamname: discord.CategoryChannel,
    add_member: discord.Member,
    add_member2: discord.Member = None
):
    if interaction.user not in teamname.overwrites:
        await interaction.response.send_message(
            "You cannot add someone to a team you are not a member off",
            ephemeral=True
        )
        return
    if add_member in teamname.overwrites or add_member2 in teamname.overwrites:
        await interaction.response.send_message(
            f"{add_member} or {add_member2 if add_member2 is not None else ''} are already part of {teamname}",
            ephemeral=True
        )
        return

    
    await interaction.response.defer()

    members = [add_member, add_member2]
    members = list({m.id:m for m in members if m is not None}.values())

    permissions = discord.PermissionOverwrite(
        view_channel=True, connect=True, speak=True, send_messages=True
    )
    try:
        for m in members:
            await teamname.set_permissions(m, overwrite=permissions)
            for channel in teamname.channels:
                await channel.set_permissions(m, overwrite=permissions)

        names = ", ".join(m.mention for m in members)
        await interaction.followup.send(f"Added {names} to **{teamname}**.")

        text_channel = discord.utils.get(teamname.text_channels, name="text")
        if text_channel:
            await text_channel.send(f"Welcome to the team, {names}!")
    except discord.Forbidden:
        await interaction.followup.send("I don't have permission...")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")



bot.run(token, log_handler=handler, log_level=logging.DEBUG)