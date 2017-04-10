##!/bin/bash
#SENSOR="systemctl status sensor"
#LTE="systemctl status lte"
#CC="$SENSOR && $LTE && echo 'services are alright'"
#
## check 2 times if sensor and lte services are alive
## if not the rpi must be reboot
#while true
#do
#
#if $CC; then
#   sleep 10
#   if $CC; then
#       $("/sbin/reboot")
#   fi
#fi
#sleep 20
#
#done

