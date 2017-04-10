#!/bin/bash
sudo echo '[Unit]
Description=Lte module service

[Service]
ExecStartPre=ls /dev/cdc-wdm0 || echo "cannot see the lte module, retrying..."
ExecStart=/home/pi/lte-daemon
Restart=on-failure
RestartSec=5


[Install]
WantedBy=multi-user.target

'> /lib/systemd/system/lte.service
sudo echo '[Unit]
Description=read sensor and send data via websocket

[Service]
ExecStart=/home/pi/sensor-reader/main.py
WorkingDirectory=/home/pi/sensor-reader
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

' > /lib/systemd/system/sensor.service
sudo systemctl daemon-reload