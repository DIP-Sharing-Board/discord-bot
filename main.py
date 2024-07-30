# datetime
from datetime import datetime
from zoneinfo import ZoneInfo
import pytz

# discord
from discord.ext import commands
import discord
import re

# env
from dotenv import dotenv_values
import os

# python typing
from typing import List

# hash
import hashlib

# Web Scrape
from scrapy.utils.log import configure_logging

# sqlalchemy
from sqlalchemy import select, update

# Import from local
from ActivityScraper import ActivityScraper
from database import Base, session, Camp, Competition, Other

config = dotenv_values(".env")

CAMP_CHANNEL_NAME = config.get("CAMP_CHANNEL_NAME") if config else os.getenv("CAMP_CHANNEL_NAME")
COMP_CHANNEL_NAME = config.get("COMP_CHANNEL_NAME") if config else os.getenv("COMP_CHANNEL_NAME")
OTHER_CHANNEL_NAME = config.get("OTHER_CHANNEL_NAME") if config else os.getenv("OTHER_CHANNEL_NAME")
BOT_TOKEN = config.get("BOT_TOKEN") if config else os.getenv("BOT_TOKEN")
CHANNELS_ID = config.get("CHANNELS_ID").split(',') if config else os.getenv("CHANNELS_ID").split(',')
URL_REGEX = re.compile(
    r'http[s]?://'  # http:// or https://
    r'(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|'  # domain and allowed characters
    r'(?:%[0-9a-fA-F][0-9a-fA-F]))+'  # and hex characters
    r'(?:/[a-zA-Z0-9#\-_./?=&%]*)?'  # optional path
    r'(?!.*\s)'  # no spaces allowed
)

channels: List[discord.TextChannel | None] = []

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("DIP Sharing Board bot is ready")
    for id in CHANNELS_ID:
        channel = bot.get_channel(int(id))
        await channel.send("Hello! DIP Sharing Board bot is ready!")
    for id in CHANNELS_ID:
        channels.append(bot.get_channel(int(id)))

@bot.listen()
async def on_message(msg):
    try:

        # Handle channel isn't in the channels list
        if msg.channel not in channels: return

        # Handle message that isn't url
        if not URL_REGEX.match(msg.content): return

        # Handle / after url and declare url
        url = msg.content if msg.content[-1] == "/" else msg.content + "/"

        # change activity type from obj to str
        activity_type = str(msg.channel)

        # hash a link to query from database
        hashLink = hashlib.md5(url.encode()).hexdigest()

        # assign model to query
        Type = Camp if activity_type == CAMP_CHANNEL_NAME else Competition if activity_type == COMP_CHANNEL_NAME else Other if activity_type == OTHER_CHANNEL_NAME else None
        
        # Handle Wrong Channel
        if Type is None: return

        # query to table based on activity type is it have hashLink
        # Build the query
        query = select(Type).filter(Type.hashLink == hashLink)

        # Execute the query
        data = session.execute(query).scalars().all()

        # if have data change updatedAt then return
        if len(data) > 0:
            # Build the update query
            update_query = update(Type).where(Type.hashLink == hashLink).values(updatedAt=datetime.now(ZoneInfo('UTC')))
            
            # Execute the update query
            session.execute(update_query)

            # Commit the transaction to save the changes
            session.commit()
            return

        # call function activity scraper
        result = ActivityScraper().run_scrape_event(url)

        # filter contrain in the requirement out ### if imageUrl is None then filter then return ## filter url out
        if result["imageUrl"] is None: return

        # handle none deadline
        deadline = None if result["deadline"] is None else result["deadline"].astimezone(pytz.utc)

        # add data to database based on activity type
        new_entry = Type(
            hashLink = hashLink,
            link =  url,
            topic = result["topic"],
            imageUrl = result["imageUrl"],
            deadline = deadline
        )

        # Add the new record to the session
        session.add(new_entry)

        # Commit the transaction
        session.commit()
    except Exception as e:
        print(f"error:{e}")

if __name__ == "__main__":
    configure_logging()
    bot.run(BOT_TOKEN)