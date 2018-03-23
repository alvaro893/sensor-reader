#!/bin/bash
# Note: the '|& tee -a "$logfile"'  line copies the ouput to both screen and logfile
workfolder="/home/pi/sensor-reader"
logfile="$workfolder/build.log"
service_files_path="$workfolder/service_files"

echo -e "Clean Log file and add to log\n\n" |& tee -a "$logfile"
echo "" > "$logfile"
echo "-------------------------------------" >> "$logfile"


echo -e "\n\nUpdate time Configuration\n\n" |& tee -a "$logfile"
apt-get install ntp -y
cat "$service_files_path/ntp.conf" > /etc/ntp.conf
systemctl restart ntp
sleep 1
ntpq -p |& tee -a "$logfile"
echo Today is `date` |& tee -a "$logfile"



echo -e "\n\nMake all files in service_files executable...\n\n" |& tee -a "$logfile"
chmod -R +x "$service_files_path"


echo -e "\n\nRun main script and log it\n\n" |& tee -a "$logfile"
"$service_files_path/main-script.sh" |& tee -a "$logfile"

echo -e "\n\nCheck if we need to pytinstall opencv\n\n" |& tee -a "$logfile"
python -c 'import cv2' || "$service_files_path/install-opencv.sh" |& tee -a "$logfile"


echo -e "\n\nBuild Cython code...\n\n" |& tee -a "$logfile"
cd analysis
sudo python setup.py build_ext -b ..
cd ..

echo -e "\n\nUpdate hostname\n\n" |& tee -a "$logfile"
apt-get install jq -y
"$service_files_path/update_hostname.sh" |& tee -a "$logfile"

echo -e "\n\nRestart sensor service\n\n"  |& tee -a "$logfile"
"$service_files_path/reset-sensor.sh" |& tee -a "$logfile"

echo "------Build.sh script done" |& tee -a "$logfile"
