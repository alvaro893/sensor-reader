#!/bin/bash
#rebootd="/reboot-daemon"
home="/home/pi"
workfolder="$home/sensor-reader"
logfile="$workfolder/build.log"
service_files="service_files"
service_files_path="$workfolder/service_files"
lted="lte-daemon"
systemdscript="systemd-services.sh"



# Called from Raspberry_commands update() function
# This will install all dependencies, run it as root
# Create env file
ENV_FILE=".env.json"
if [ ! -f "$ENV_FILE" ]; then
    cat "$service_files_path/template.json" > "$ENV_FILE"
    echo "added $ENV_FILE file"
fi

# Set wireless LAN password and user
cat "$service_files_path/wpa_supplicant.conf" > /etc/wpa_supplicant/wpa_supplicant.conf

# install packages
echo -e "\n\n - Installing and Updating packages (if needed)...\n\n" |& tee -a "$logfile"
apt-get update -y
apt-get install ntpdate python-dev libusb-dev ntp jq -y
sudo pip install pip --upgrade
sudo pip install -r requirements.txt --upgrade

echo -e "\n\n - Update time Configuration\n\n" |& tee -a "$logfile"
cat "$service_files_path/ntp.conf" > /etc/ntp.conf
systemctl restart ntp
sleep 1
ntpq -p |& tee -a "$logfile"
echo Today is `date` |& tee -a "$logfile"

# set the Helsinki hourzone
echo -e "\n\n - Update time zone to +2 (Helsinki)\n\n" |& tee -a "$logfile"
sudo cp /usr/share/zoneinfo/Europe/Helsinki /etc/localtime


# copy scripts and add permissions
cat "$service_files_path/$lted" > "$home/$lted"
chmod +x "$home/$lted"

# update crontab jobs
crontab -r  # remove file
(crontab -l 2>/dev/null; echo "0 4   *   *   *    /sbin/shutdown -r +5") | crontab -  # reboot at 4 am


echo -e "\n\n - Check if we need to pytinstall opencv\n\n" |& tee -a "$logfile"
python -c 'import cv2' || "$service_files_path/install-opencv.sh" |& tee -a "$logfile"


echo -e "\n\n - Build Cython code...\n\n" |& tee -a "$logfile"
cd analysis
sudo python setup.py build_ext -b ..
cd ..

echo -e "\n\n - Update hostname\n\n" |& tee -a "$logfile"
"$service_files_path/update_hostname.sh" |& tee -a "$logfile"

echo -e "\n\n - Restart sensor service\n\n"  |& tee -a "$logfile"
"$service_files_path/reset-sensor.sh" |& tee -a "$logfile"

# install teensy cli loader if not exist
TEENSY_CLI_DIR="$home/teensy_loader_cli"
if [ ! -d "$TEENSY_CLI_DIR" ]; then
    git clone https://github.com/alvaro893/teensy_loader_cli "$TEENSY_CLI_DIR"
    https://github.com/alvaro893/teensy_loader_cli
    echo "created $TEENSY_CLI_DIR"
fi

# update systemd services
"$service_files_path/$systemdscript"

