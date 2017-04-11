#!/bin/bash
workfolder="/home/pi/sensor-reader"
logfile="$workfolder/build.log"
service_files_path="$workfolder/service_files"

# make all files in service_files executable
chmod -R +x "$service_files_path"

# clean and add to log
echo "" > "$logfile"
echo "-------------------------------------" >> "$logfile"
date >> "$logfile"


# run main script and log it
"./$service_files_path/main-script.sh" >> "$logfile"
