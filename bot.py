import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv

# Load .env token
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")

# !join
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"🔊 Joined {channel}")
    else:
        await ctx.send("❌ You must be in a voice channel to use this command.")

# !leave
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left the voice channel.")
    else:
        await ctx.send("❌ I'm not in a voice channel.")

# !play
@bot.command()
async def play(ctx, *, url):
    vc = ctx.voice_client
    if not vc:
        if ctx.author.voice:
            vc = await ctx.author.voice.channel.connect()
        else:
            return await ctx.send("❌ Join a voice channel first!")

    await ctx.send("⏳ Searching for audio...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                info = info['entries'][0]  # First search result
            audio_url = info['url']
            title = info.get('title', 'Unknown Title')

        ffmpeg_options = {
            'options': '-vn'
        }

        source = await discord.FFmpegOpusAudio.from_probe(audio_url, **ffmpeg_options)
        vc.play(source, after=lambda e: print(f"Player error: {e}" if e else None))

        await ctx.send(f"🎶 Now playing: **{title}**")

    except Exception as e:
        await ctx.send(f"❌ Error while playing: `{str(e)}`")
        print("Play command error:", e)

# Run bot
bot.run(TOKEN)
