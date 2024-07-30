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
from sqlalchemy.exc import SQLAlchemyError

# logging
import logging

# Import from local
from ActivityScraper import ActivityScraper
from database import Base, session, Camp, Competition, Other

# async
import asyncio

class DIPSharingBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = dotenv_values(".env")
        self.CAMP_CHANNEL_NAME = self.config.get("CAMP_CHANNEL_NAME") if self.config else os.getenv("CAMP_CHANNEL_NAME")
        self.COMP_CHANNEL_NAME = self.config.get("COMP_CHANNEL_NAME") if self.config else os.getenv("COMP_CHANNEL_NAME")
        self.OTHER_CHANNEL_NAME = self.config.get("OTHER_CHANNEL_NAME") if self.config else os.getenv("OTHER_CHANNEL_NAME")
        self.CHANNELS_ID = self.config.get("CHANNELS_ID").split(',') if self.config else os.getenv("CHANNELS_ID").split(',')
        self.URL_REGEX = re.compile(
            r'http[s]?://'  # http:// or https://
            r'(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|'  # domain and allowed characters
            r'(?:%[0-9a-fA-F][0-9a-fA-F]))+'  # and hex characters
            r'(?:/[a-zA-Z0-9#\-_./?=&%]*)?'  # optional path
            r'(?!.*\s)'  # no spaces allowed
        )
        self.channels = []

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("DIP Sharing Bot is ready")
        for id in self.CHANNELS_ID:
            channel = self.bot.get_channel(int(id))
            await channel.send("Hello! DIP Sharing Bot is ready!")
            self.channels.append(channel)

    @commands.Cog.listener()
    async def on_message(self, msg):
        try:
            # Handle channel isn't in the channels list
            if msg.channel not in self.channels: return

            # Handle message that isn't url
            if not self.URL_REGEX.match(msg.content): return

            # Handle / after url and declare url
            url = msg.content if msg.content[-1] == "/" else msg.content + "/"

            # change activity type from obj to str
            activity_type = msg.channel.name

            # hash a link to query from database
            hashLink = hashlib.md5(url.encode()).hexdigest()

            # assign model to query
            Type = None
            if activity_type == self.CAMP_CHANNEL_NAME:
                Type = Camp
            elif activity_type == self.COMP_CHANNEL_NAME:
                Type = Competition
            elif activity_type == self.OTHER_CHANNEL_NAME:
                Type = Other
            
            # Handle Wrong Channel
            if Type is None: return

            # query to table based on activity type is it have hashLink
            query = select(Type).filter(Type.hashLink == hashLink)
            data = session.execute(query).scalars().all()

            if len(data) > 0:
                update_query = update(Type).where(Type.hashLink == hashLink).values(updatedAt=datetime.now(ZoneInfo('UTC')))
                session.execute(update_query)
                session.commit()
                return

            result = ActivityScraper().run_scrape_event(url)

            if result["imageUrl"] is None: return

            deadline = None if result["deadline"] is None else result["deadline"].astimezone(pytz.utc)

            new_entry = Type(
                hashLink = hashLink,
                link =  url,
                topic = result["topic"],
                imageUrl = result["imageUrl"],
                deadline = deadline
            )

            session.add(new_entry)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    config = dotenv_values(".env")
    BOT_TOKEN = config.get("BOT_TOKEN") if config else os.getenv("BOT_TOKEN")

    configure_logging()

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
   
    # Correctly awaiting the add_cog method
    async def main():
        await bot.add_cog(DIPSharingBot(bot))
        await bot.start(os.getenv("BOT_TOKEN"))

    asyncio.run(main())