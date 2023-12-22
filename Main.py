import discord
from discord.ext import commands
from config import settings
import asyncio
import yt_dlp as youtube_dl
from collections import deque

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = settings['prefix'], intents = intents)
bot.queue = deque()

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')





@bot.command(name='play')
async def play(ctx, *, url):
    voice_channel = ctx.author.voice.channel
    async with ctx.typing():
        from YTDLS import YTDLSource
        player = await YTDLSource.from_url(url, loop=bot.loop)
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            ctx.voice_channel = await voice_channel.connect()

        bot.queue.append(player)
        if not ctx.voice_client.is_playing():
            await play_next(ctx)

    await ctx.send(f'Added to queue: {player.title}')

async def play_next(ctx):
    if bot.queue:
        player = bot.queue.popleft()
        ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop) if e else None)
        await ctx.send(f'Now playing: {player.title}')
    else:
        await ctx.send("Queue is empty.")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped the current track.")
        await play_next(ctx)
    else:
        await ctx.send("Nothing is currently playing.")














@bot.command(name='volume')
async def volume(ctx, vol: int):
    if ctx.voice_client is None:
        return await ctx.send("I'm not connected to a voice channel.")
    
    if 0 <= vol <= 100:
        ctx.voice_client.source.volume = vol / 100
        await ctx.send(f"Volume set to {vol}%")
    else:
        await ctx.send("Volume must be between 0 and 100")

@bot.command(name='leave')
async def leave(ctx):
    voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_channel.is_connected():
        await voice_channel.disconnect()

bot.run(settings['token'])
