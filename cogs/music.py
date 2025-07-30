import discord
from discord.ext import commands
import yt_dlp
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}
        self.ytdl_format_options = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }
        self.ffmpeg_options = {
            'options': '-vn'
        }
        self.ytdl = yt_dlp.YoutubeDL(self.ytdl_format_options)

    async def ensure_voice(self, ctx):
        """Ensure the bot is connected to a voice channel."""
        if ctx.author.voice:
            if ctx.voice_client is None:
                await ctx.author.voice.channel.connect()
        else:
            await ctx.send("❌ You must be in a voice channel to use this command.")
            return False
        return True

    async def play_next(self, ctx):
        """Play the next song in the queue."""
        if self.queue.get(ctx.guild.id):
            url = self.queue[ctx.guild.id].pop(0)
            await self.play_song(ctx, url)
        else:
            await ctx.voice_client.disconnect()

    async def play_song(self, ctx, url):
        """Play a single song from a given URL."""
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))
        if 'entries' in data:
            data = data['entries'][0]

        song_url = data['url']
        title = data.get('title', 'Unknown title')

        ctx.voice_client.stop()
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(song_url, **self.ffmpeg_options),
            after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)
        )
        await ctx.send(f"🎶 **Now playing:** `{title}`")

    @commands.command(name="play", help="Plays a song from YouTube")
    async def play(self, ctx, *, query: str):
        """Search or play a YouTube link."""
        if not await self.ensure_voice(ctx):
            return

        if "youtube.com" not in query and "youtu.be" not in query:
            query = f"ytsearch:{query}"

        if ctx.guild.id not in self.queue:
            self.queue[ctx.guild.id] = []

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            self.queue[ctx.guild.id].append(query)
            await ctx.send("✅ Added to the queue.")
        else:
            await self.play_song(ctx, query)

    @commands.command(name="skip", help="Skip the current song")
    async def skip(self, ctx):
        """Skip the currently playing song."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭ Skipped the song.")
        else:
            await ctx.send("❌ Nothing is playing.")

    @commands.command(name="pause", help="Pause the current song")
    async def pause(self, ctx):
        """Pause playback."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸ Music paused.")
        else:
            await ctx.send("❌ Nothing is playing to pause.")

    @commands.command(name="resume", help="Resume paused music")
    async def resume(self, ctx):
        """Resume playback."""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶ Music resumed.")
        else:
            await ctx.send("❌ No music is paused.")

    @commands.command(name="stop", help="Stop playback and leave the channel")
    async def stop(self, ctx):
        """Stop playback and clear queue."""
        if ctx.voice_client:
            self.queue[ctx.guild.id] = []
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Music stopped and disconnected.")
        else:
            await ctx.send("❌ I'm not connected to a voice channel.")

async def setup(bot):
    await bot.add_cog(Music(bot))
