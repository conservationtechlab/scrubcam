#!/bin/bash

echo "---INSTALLING PYCORAL---"

echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt update
sudo apt -y install libedgetpu1-std
sudo apt -y install python3-pycoral

echo -e "\nPROMPT: If you can unplug/replug Coral USB accelerator do so now.  If you can't a reboot will probably do the trick.  Should I reboot the host? (yes/no)"
read confirmation

if [ "$confirmation" == "yes" ]; then
    echo "Rebooting the host..."
    sudo reboot now
else
    echo "Will not do reboot."
fi
