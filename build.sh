#!/bin/bash
workfolder="/home/pi/sensor-reader"
logfile="$workfolder/build.log"
service_files_path="$workfolder/service_files"

echo "clean Log file and add to log"
echo "" > "$logfile"
echo "-------------------------------------" >> "$logfile"

echo "update time"
"$service_files_path/synctime.sh"
date >> "$logfile"

echo "make all files in service_files executable..."
chmod -R +x "$service_files_path"


echo "run main script and log it"
"$service_files_path/main-script.sh" |& tee -a "$logfile"

echo "check if we need to install opencv"
python -c 'import cv2' || echo "need to install openCV" && "$service_files_path/install-opencv.sh" |& tee -a "$logfile"


echo "Build Cython code..."
cd analysis
sudo python setup.py build_ext -b ..
cd ..

echo "------Build.sh script done" |& tee -a "$logfile"
