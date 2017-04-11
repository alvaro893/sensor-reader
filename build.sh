#!/bin/bash
workfolder="/home/pi/sensor-reader"
logfile="$workfolder/build.log"
service_files_path="$workfolder/service_files"

# clean and add to log
echo "" > "$logfile"
echo "-------------------------------------" >> "$logfile"

# update time
"$service_files_path/synctime.sh"
date >> "$logfile"

# make all files in service_files executable
chmod -R +x "$service_files_path"

# run main script and log it
"$service_files_path/main-script.sh" |& tee -a "$logfile"
