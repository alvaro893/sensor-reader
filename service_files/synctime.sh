#!/bin/bash
# updates time from http request
sudo date +%s -s @`curl http://currentmillis.com/time/seconds-since-unix-epoch.php`
currentmillis.com/time/seconds-since-unix-epoch.php

echo "---------Time synchronized"