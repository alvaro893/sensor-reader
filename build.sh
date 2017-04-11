#!/bin/bash
workfolder="/home/pi/sensor-reader"
logfile="$workfolder/build.log"

# make all files in service_files executable
chmod -R +x "$workfolder/service_files"

# clean and add to log
echo "" > "$logfile"
echo "-------------------------------------" >> "$logfile"
date >> "$logfile"


# run main script and log it
./main-script.sh >> "$logfile"
