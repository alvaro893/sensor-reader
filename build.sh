#!/bin/bash
logfile="/home/pi/build.log"
echo "-------------------------------------" >> "$logfile"
date >> "$logfile"
# run main script
./main-script.sh >> "$logfile"
