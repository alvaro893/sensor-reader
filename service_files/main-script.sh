#!/bin/bash
#rebootd="/reboot-daemon"
home="/home/pi"
workfolder="$home/sensor-reader"
service_files="service_files"
service_files_path="$workfolder/service_files"
lted="lte-daemon"
systemdscript="systemd-services.sh"



# Called from Raspberry_commands update() function
# This will install all dependencies, run it as root
git pull origin raspberry
# Create env file
ENV_FILE=".env.json"
if [ ! -f "$ENV_FILE" ]; then
    echo '{"WS_PASSWORD":"", "URL":""}' > "$ENV_FILE"
    echo "added $ENV_FILE file"
fi

# install packages
sudo apt-get update -y
apt-get install ntpdate python-dev libusb-dev -y
sudo pip install pip --upgrade
sudo pip install -r requirements.txt --upgrade

# set the Helsinki hourzone
sudo cp /usr/share/zoneinfo/Europe/Helsinki /etc/localtime


# copy scripts and add permissions
cp "$service_files_path/$lted" "$home/$lted"
chmod +x "$home/$lted"

# update crontab jobs
crontab -r  # remove file
(crontab -l 2>/dev/null; echo "0 4   *   *   *    /sbin/shutdown -r +5") | crontab -  # reboot at 4 am
#(crontab -l 2>/dev/null; echo "59 *   *   *   *    /home/pi/synctime") | crontab -  # update time every hour, not working

# install teensy cli loader if not exist
TEENSY_CLI_DIR="$home/teensy_loader_cli"
if [ ! -d "$TEENSY_CLI_DIR" ]; then
    git clone https://github.com/alvaro893/teensy_loader_cli "$TEENSY_CLI_DIR"
    https://github.com/alvaro893/teensy_loader_cli
    echo "created $TEENSY_CLI_DIR"
fi

# update systemd services
"$service_files_path/$systemdscript"


echo "Done"
