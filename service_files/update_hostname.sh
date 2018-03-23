#!/usr/bin/env bash


# set the camera name as hostname
newhostname=`jq '.CAMERA_NAME' /home/pi/sensor-reader/.env.json`
# remove non alpha-numerics
newhostname=`echo "$newhostname" | sed 's/[^a-zA-Z0-9]//g'`
# to lowercase
newhostname=`echo "$newhostname" | awk '{print tolower($0)}'`

# update /etc/hostname
echo "$newhostname" > /etc/hostname

# update /etc/hosts
echo  "
127.0.0.1     localhost
::1           localhost ip6-localhost ip6-loopback
ff02::1       ip6-allnodes
ff02::2       ip6-allrouters

127.0.1.1     $newhostname
" > /etc/hosts

# and finally
/etc/init.d/hostname.sh start