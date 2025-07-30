import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# =======================
# CONFIG
# =======================
API_URL = "https://api.tracker.gg/api/v2/marvel-rivals/standard/profile/ign/jimby3"
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


# =======================
# EVENTS
# =======================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")


# =======================
# VOICE COMMANDS
# =======================
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"🔊 Joined {channel}")
    else:
        await ctx.send("❌ You must be in a voice channel to use this command.")


@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left the voice channel.")
    else:
        await ctx.send("❌ I'm not in a voice channel.")


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
                info = info['entries'][0]
            audio_url = info['url']
            title = info.get('title', 'Unknown Title')

        ffmpeg_options = {'options': '-vn'}
        source = await discord.FFmpegOpusAudio.from_probe(audio_url, **ffmpeg_options)
        vc.play(source, after=lambda e: print(f"Player error: {e}" if e else None))

        await ctx.send(f"🎶 Now playing: **{title}**")

    except Exception as e:
        await ctx.send(f"❌ Error while playing: `{str(e)}`")
        print("Play command error:", e)


# =======================
# MARVEL RIVALS STATS COMMAND
# =======================
def fetch_rivals_data():
    """Uses Selenium to fetch data from Tracker.gg and return JSON"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    data = None

    try:
        driver.get(API_URL)
        time.sleep(3)
        response_text = driver.find_element("tag name", "pre").text
        data = json.loads(response_text)
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
    finally:
        driver.quit()

    return data


@bot.command()
async def stats(ctx):
    await ctx.send("🔄 Fetching latest stats, please wait...")
    data = fetch_rivals_data()
    if not data:
        await ctx.send("⚠️ Could not fetch data at this time.")
        return

    username = data.get("data", {}).get("platformInfo", {}).get("platformUserHandle", "Unknown")
    segments = data.get("data", {}).get("segments", [])
    wins = "N/A"
    kills = "N/A"
    matches_played = "N/A"

    if segments:
        stats = segments[0].get("stats", {})
        wins = stats.get("wins", {}).get("value", "N/A")
        kills = stats.get("kills", {}).get("value", "N/A")
        matches_played = stats.get("matchesPlayed", {}).get("value", "N/A")

    embed = discord.Embed(title=f"Marvel Rivals Stats for {username}", color=0x00ffcc)
    embed.add_field(name="🏆 Wins", value=wins, inline=True)
    embed.add_field(name="🔫 Kills", value=kills, inline=True)
    embed.add_field(name="🎮 Matches Played", value=matches_played, inline=True)
    await ctx.send(embed=embed)


# =======================
# RUN BOT
# =======================
bot.run(TOKEN)
