#!/bin/bash

# This will install all dependencies, run it as root
# Tested in Ubuntu 14.04 and 16.04

# Create env file
ENV_FILE=".env.json"
if [ ! -f "$ENV_FILE" ]; then
    echo "{}" > "$ENV_FILE"
    echo "added $ENV_FILE file"
fi

# PyQT must be installed from Ubuntu repository
sudo apt-get install python-qt4 python-pip -y
sudo pip install pip --upgrade
sudo pip install -r requirements.txt --upgrade

