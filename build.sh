#!/bin/bash
# Note: the '|& tee -a "$logfile"'  statements copies the ouput to both screen and logfile

workfolder="/home/pi/sensor-reader"
logfile="$workfolder/build.log"
service_files_path="$workfolder/service_files"

echo -e " - Clean Log file\n\n" |& tee -a "$logfile"
echo "" > "$logfile"
echo "-------------------------------------" >> "$logfile"

if [ "$EUID" -ne 0 ]
  then echo "Please run as root" |& tee -a "$logfile"
  exit
fi

echo -e "\n\n - Get last version from git...\n\n" |& tee -a "$logfile"
git -C "$workfolder" checkout -- . # this removes any changes made to tracked files
git -C "$workfolder" fetch
git -C "$workfolder" pull origin raspberry


echo -e "\n\ - nMake all files in service_files executable...\n\n" |& tee -a "$logfile"
chmod -R +x "$service_files_path"

echo -e "\n\nRun main script and log it\n\n" |& tee -a "$logfile"
"$service_files_path/main-script.sh" |& tee -a "$logfile"


echo "------Build.sh script done" |& tee -a "$logfile"
