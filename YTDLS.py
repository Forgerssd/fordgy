import yt_dlp as youtube_dl
import discord
from discord.ext import commands
import asyncio

youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'verbose': True,
    'nocheckcertificate': True,    
}
ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.1):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.volume = volume

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True, bot=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            entries = data['entries']
            for entry in entries:
                url = entry['url']
                filename = ytdl.prepare_filename(entry) if not stream else url
                entry['url'] = filename
                player = cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=entry)
                bot.queue.append(player)

            return bot.queue[-1]  # Return the last player in the queue (optional)
        else:
            if stream:
                filename = data['url']
            else:
                filename = ytdl.prepare_filename(data)
                data['url'] = filename  # Update the data's URL to the actual file path
        
            player = cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
            bot.queue.append(player)
            return player