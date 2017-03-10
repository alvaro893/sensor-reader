#!/usr/bin/env bash
# This will install all dependencies, run it as root

# Create env file
ENV_FILE=".env.json"
if [ ! -f "$ENV_FILE" ]; then
    echo '{"WS_PASSWORD":"", "URL":""}' > "$ENV_FILE"
    echo "added $ENV_FILE file"
fi

sudo apt-get update -y
sudo apt-get install python-dev -y
sudo pip install pip --upgrade
sudo pip install -r requirements.txt --upgrade