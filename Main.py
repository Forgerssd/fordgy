import os
import discord
from discord.ext import commands
from config import settings
import asyncio
import yt_dlp as youtube_dl
from collections import deque
from YTDLS import YTDLSource

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=settings['prefix'], intents=intents)
bot.queue = deque()

global playVol
playVol = 0.1
global stop_playing
stop_playing = False

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

async def play_next(ctx, player):
    global stop_playing
    if bot.queue:
        next_player = bot.queue.popleft()
        ctx.voice_client.play(next_player, after=lambda e: bot.loop.create_task(play_next(ctx, next_player)) if e else None)
        ctx.voice_client.source.volume = playVol
        # Отправляем первое сообщение и сохраняем объект сообщения
        message = await ctx.send(f'Now playing: {next_player.title}')
        # Дожидаемся окончания трека
        while ctx.voice_client and ctx.voice_client.is_playing() and not stop_playing:  
            await asyncio.sleep(1)

        stop_playing = False

        # После окончания трека редактируем сообщение
        await message.edit(content=f'Now playing: {next_player.title}')

        # После окончания трека вызываем play_next
        await play_next(ctx, next_player)
    else:
        # Если очередь пуста, редактируем первое сообщение
        await ctx.send("Queue is empty.")

@bot.command(name='play')
async def play(ctx, *, url):
    voice_channel = ctx.author.voice.channel

    player = await YTDLSource.from_url(url, loop=bot.loop, bot=bot)
    player.on_end = lambda: bot.loop.create_task(play_next(ctx, player))
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        await voice_channel.connect()
    
    print(f'Queue length: {len(bot.queue)}')  # Добавим отладочный вывод

    # Добавим небольшую асинхронную задержку
    await asyncio.sleep(1)

    # Проверим, играет ли аудио
    if not ctx.voice_client.is_playing():
        await play_next(ctx, player)
    
    # Если есть треки в очереди, редактируем первое сообщение
    if bot.queue:
        await ctx.send(f'Now playing: {player.title}')




@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    else: 
        await ctx.send("Nothing is currently playing.")
    
    await play_next(ctx, None)

@bot.command(name='volume')
async def volume(ctx, vol: int):
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        return await ctx.send("I'm not connected to a voice channel.")
    
    if 0 <= vol <= 100:
        global playVol
        playVol = vol / 100
        ctx.voice_client.source.volume = playVol
        await ctx.send(f"Volume set to {vol}%")
    else:
        await ctx.send("Volume must be between 0 and 100")

@bot.command(name='leave')
async def leave(ctx):
    #voice_channel = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    global stop_playing
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        stop_playing = True
        bot.queue.clear()
    if ctx.voice_client.is_connected():
        await ctx.voice_client.disconnect()

@bot.event
async def on_voice_state_update(member, before, after):
    if not member.bot and after.channel is None and bot.voice_clients:
        await play_next(bot.voice_clients[0])

bot.run(settings['token'])
