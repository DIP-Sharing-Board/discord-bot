from discord.ext import commands
import discord
import re
from dotenv import dotenv_values
from typing import List
from mock_func import get_data
import os

config = dotenv_values(".env")
BOT_TOKEN = config["BOT_TOKEN"] if config else os.environ["BOT_TOKEN"]
CHANNELS_ID = config["CHANNELS_ID"].split(',') if config else os.environ["CHANNELS_ID"].split(',')
URL_REGEX = re.compile(
    r'http[s]?://'  # http:// or https://
    r'(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|'  # domain and allowed characters
    r'(?:%[0-9a-fA-F][0-9a-fA-F]))+'  # and hex characters
    r'(?:/[a-zA-Z0-9#\-_./?=&%]*)?'  # optional path
    r'(?!.*\s)'  # no spaces allowed
)

channels: List[discord.TextChannel] = []

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("DIP Sharing Board bot is ready")
    channel = bot.get_channel(int(CHANNELS_ID[0]))
    await channel.send("Hello! DIP Sharing Board bot is ready!")
    for id in CHANNELS_ID:
        channels.append(bot.get_channel(int(id)))

@bot.listen()
async def on_message(msg):
    if msg.channel not in channels: return
    if not URL_REGEX.match(msg.content): return
    print(f"link: {msg.content} \ntype: {msg.channel}")
    url = msg.content
    activity_data = get_data(url) # web scrap the url to get all needed data

bot.run(BOT_TOKEN)