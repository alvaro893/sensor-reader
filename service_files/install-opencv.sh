#!/usr/bin/env bash
echo "installing openCV 3.1.0..."
sudo apt-get install libtiff5-dev libjasper-dev libpng12-dev libavcodec-dev \
libavformat-dev libswscale-dev libv4l-dev libatlas-base-dev gfortran libgtk2.0-dev -y && \
wget "https://github.com/jabelone/OpenCV-for-Pi/raw/master/latest-OpenCV.deb" && \
sudo dpkg -i latest-OpenCV.deb && \
rm -f latest-OpenCV.deb