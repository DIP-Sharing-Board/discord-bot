#!/bin/sh

# Read the secret from the file and export it as an environment variable
export BOT_TOKEN=$(cat /run/secrets/bot-token)
export CHANNELS_ID=$(cat /run/secrets/channels-id)
export MYSQL_ROOT_PASSWORD=$(cat /run/secrets/db-password)
# Now you can start your main application
exec python main.py