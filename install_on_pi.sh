#!/bin/bash

pip install .[pi]
sudo apt install libopencv-dev
sudo apt -y install libjasper-dev libatlas-base-dev libqt4-dev

# Enable the camera, if not already enabled in the boot config file.
echo -e "\nChecking camera status..."

if grep -q "start_x=0" /boot/config.txt
then
    echo "Camera is disabled."
    sudo sed -i "s/start_x=0/start_x=1/g" /boot/config.txt
    echo "Enabling camera."
else
    echo "Camera is already enabled."
fi

# Prompt user to reboot Pi.
echo -e "\nIn order for some changes to take effect, a reboot is required."
echo "Would you like to reboot?"

select yn in "Yes" "No"
do
    case $yn in
        Yes ) sudo reboot;;
        No ) exit;;
    esac
done
