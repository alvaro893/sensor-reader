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

echo "installing openCV 3.1.0"
sudo apt-get install libtiff5-dev libjasper-dev libpng12-dev libavcodec-dev \
libavformat-dev libswscale-dev libv4l-dev libatlas-base-dev gfortran libgtk2.0-dev -y && \
wget "https://github.com/jabelone/OpenCV-for-Pi/raw/master/latest-OpenCV.deb" && \
sudo dpkg -i latest-OpenCV.deb && /
rm -f latest-OpenCV.deb

echo "Build Cython code..."
cd analysis
sudo python setup.py build_ext -b ..
cd ..

echo "------Build.sh script done" |& tee -a "$logfile"
