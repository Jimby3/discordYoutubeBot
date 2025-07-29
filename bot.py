import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv

# Load token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Set up bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user.name}")

# /join command
@tree.command(name="join", description="Make the bot join your voice channel")
async def join(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message(f"🔊 Joined {channel}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ You're not in a voice channel.", ephemeral=True)

# /leave command
@tree.command(name="leave", description="Make the bot leave the voice channel")
async def leave(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("👋 Left the voice channel.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ I'm not in a voice channel.", ephemeral=True)

# /play command
@tree.command(name="play", description="Play audio from a YouTube URL or search query")
@app_commands.describe(query="YouTube URL or search term")
async def play(interaction: discord.Interaction, query: str):
    vc = interaction.guild.voice_client
    if not vc:
        if interaction.user.voice:
            vc = await interaction.user.voice.channel.connect()
        else:
            return await interaction.response.send_message("❌ Join a voice channel first!", ephemeral=True)

    await interaction.response.send_message("⏳ Searching for audio...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]  # First search result

            audio_url = info['url']
            title = info.get('title', 'Unknown Title')

        ffmpeg_options = {
            'options': '-vn'
        }

        source = await discord.FFmpegOpusAudio.from_probe(audio_url, **ffmpeg_options)
        vc.play(source, after=lambda e: print(f"Player error: {e}" if e else None))

        await interaction.followup.send(f"🎶 Now playing: **{title}**")

    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")
        print("Error in /play:", e)

# Run bot
bot.run(TOKEN)
