# Overview

Control code and utilities for the ScrubCam, an edge-AI-enabled field
wildlife camera system.

# Hardware

The target hardware for the field device is a Raspberry Pi 4 Model B
single board computer with a Picamera-style camera, a Google Coral USB
Accelerator, and the AdaFruit PiTFT screen (2.8" resistive touch model
with 4 GPIO-connected buttons) attached. Typically several storage
devices are connected via the USB ports on the Pi (e.g. uSD card
readers). This hardware is typically integrated into a larger assembly
that includes a weatherproof enclosure and batteries and--in some
variants--a charger controller with external solar panels.

# Operating System

Currently system runs on Raspian Stretch and Buster.  Problems have
been encountered with Bullseye.

# Setup

### Install virtualenv virtualenvwrapper

     sudo pip3 install virtualenv virtualenvwrapper

### Set up virtualenv and virtualenvwrapper 

    echo -e "\n# Virtualenv and virtualenvwrapper stuff" >> ~/.bashrc
    echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bashrc
    echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> ~/.bashrc
    echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc
    source ~/.bashrc

### Create virtual environment for scrubcam project

     mkvirtualenv scrubcam_env

Note that DenCam requires Python 3 so if the default on your system is
Python 2 (it is on Stretch and Buster), make sure the virtual
environment will use Python 3:

      mkvirtualenv scrubcam_env -p python3

### Activate virtual environment (not necessary if you just made it)

     workon scrubcam_env

### Clone the scrubcam repo

     git clone https://github.com/icr-ctl/scrubcam.git

### Update apt package sources list

     sudo apt update

### Install scrubcam dependencies

     cd ~/scrubcam
     ./install.sh

### Set up edgetpu dependencies
     curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
     echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
     curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
     sudo apt-get update
     sudo apt-get install libedgetpu1-std
     sudo apt-get install python3-edgetpu

     # Reboot the pi
     sudo reboot now
     # Then create symlink into our virtualenv
     dpkg -L python3-edgetpu

     # Find a line like "/usr/lib/python3/dist-packages/edgetpu"
     # We will symlink this into our virtualenv
     cd ~/.virtualenvs/[virtualenv_name]/lib/python3.7/site-packages/
     ln -s /usr/lib/python3/dist-packages/edgetpu/ edgetpu
     # Then install the examples
     sudo apt-get install edgetpu-examples
     sudo chmod a+w /usr/share/edgetpu/examples


**Note: For this line, be sure that you replace [virtualenv_name] with the name of
your virtual environment.**

     cd ~/.virtualenvs/[virtualenv_name]/lib/python3.7/site-packages/

Also note that `.virtualenvs` is the default location that `mkvirtualenv` saves virtual
environments, but this may not be the case if using `venv` or `virtualenv` to create the
virtual environment. Replace `.virtualenvs` with the folder that your virtual environment
is saved to. This may be a regular folder in some instances.



# Usage

## On Raspberry Pi 

The core program in the project is `scrubcam.py` which runs on the
Raspberry Pi which is controlling the field device. It accepts a YAML
configuration file as a command line argument. There is an example
config file `./cfgs/config.yaml.example`

You can copy this example file and modify it to your specific purposes
and thus then run ScrubCam on a properly set up system (see Setup
section above for how to set up system) via:

```
Usage:
    ./scrubcam.py [OPTIONS] cfgs/YOUR_CONFIG_FILE.yaml
    
Options:
    -h, --help          Output a usage message and exit
    -c, --continue      Continue saving images to the most recent session on ScrubDash
```

## On server system 

For monitoring the activity of a ScrubCam there is also a Plotly-Dash-based
server/dashboard program called `scrubdash.py` intended to be run on a
machine on the same network (e.g. back in the lab or on a laptop in
the field). [Scrubdash](https://github.com/kaytsui/scrubdash) is used
to organize, visualize, and analyze images that are sent by ScrubCams.


