#!/bin/bash
# Note: the '|& tee -a "$logfile"'  line copies the ouput to both screen and logfile
workfolder="/home/pi/sensor-reader"
logfile="$workfolder/build.log"
service_files_path="$workfolder/service_files"

echo "clean Log file and add to log\n\n" |& tee -a "$logfile"
echo "" > "$logfile"
echo "-------------------------------------" >> "$logfile"

echo "update time"
"$service_files_path/synctime.sh"
date >> "$logfile"

echo "make all files in service_files executable...\n\n" |& tee -a "$logfile"
chmod -R +x "$service_files_path"


echo "run main script and log it\n\n" |& tee -a "$logfile"
"$service_files_path/main-script.sh" |& tee -a "$logfile"

echo "check if we need to pytinstall opencv"
python -c 'import cv2' || "$service_files_path/install-opencv.sh" |& tee -a "$logfile"


echo "Build Cython code...\n\n" |& tee -a "$logfile"
cd analysis
sudo python setup.py build_ext -b ..
cd ..

echo "Restart sensor service\n\n"  |& tee -a "$logfile"
"$service_files_path/reset-sensor.sh" |& tee -a "$logfile"

echo "------Build.sh script done" |& tee -a "$logfile"
