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

### Clone the ScrubCam repo

    git clone https://github.com/icr-ctl/scrubcam.git

### Install and set up virtualenv and virtualenvwrapper 

    sudo pip3 install virtualenv virtualenvwrapper

    echo -e "\n# Virtualenv and virtualenvwrapper stuff" >> ~/.bashrc
    echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bashrc
    echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> ~/.bashrc
    echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc
    source ~/.bashrc

### Create virtual environment for scrubcam project

Create a virtual environment named "scrubcam_env":

    mkvirtualenv scrubcam_env

Note that ScrubCam requires Python 3 so if the default on your system is
Python 2 (it is on Stretch and Buster), make sure the virtual
environment will use Python 3 by using this command instead:

    mkvirtualenv scrubcam_env -p python3

Activate virtual environment (not necessary if you just made it):

    workon scrubcam_env

### Install ScrubCam dependencies

#### Update apt package sources list

    sudo apt update

#### Run installation script

Navigate to inside of the local copy of the scrubcam code repository and run the install script:     

    cd scrubcam
    ./install.sh

#### PyCoral Packages Dependency

Scrubcam uses the Google Coral USB Accelerator and the associated
packages to interface with this hardware cannot be installed with pip
and there installation is not currently included in the install
script.

To set up the Coral, follow the directions at the project's website:

https://coral.ai/docs/accelerator/get-started/

Then to be able to access these packages from within your virtual
environment you must create symlinks within the virtual environment
files to where they are located.

Locate the packages:
    
    dpkg -L python3-pycoral
    dpkg -L python3-tflite-runtime

For each of those two packages, find a line similar to
"/usr/lib/python3/dist-packages/pycoral"

Go into the folder of the virtual environment you created (we used
scrubcam_env above) and create a symlink for each of those packages
depending on where they are actually located on your system.  For
example:

    cd ~/.virtualenvs/scrubcam_env/lib/python3.7/site-packages/
    ln -s /usr/lib/python3/dist-packages/pycoral
    ln -s /usr/lib/python3/dist-packages/tflite-runtime

Note that `.virtualenvs` is where we set up for virtual environments
to go (e.g. those created using `mkvirtualenv`) but this may not be
the case if using `venv` or `virtualenv` to create the virtual
environment. Replace `.virtualenvs` with the folder that your virtual
environment is saved to. This may be a regular folder in some
instances.
    
### Get models for testing everything is working

TODO: needs to explain how to locate and if necessary run asset download
script(s) for the test models included with pycoral

We used to get these here:

    sudo apt install edgetpu-examples
    sudo chmod a+w /usr/share/edgetpu/examples

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

## On remote server: ScrubDash

For monitoring the activity of a ScrubCam there is also a
Plotly-Dash-based server/dashboard program called `scrubdash.py`
intended to be run on a machine on the same network (e.g. back in the
lab or on a laptop in the
field). [Scrubdash](https://github.com/icr-ctl/scrubdash) is used to
organize, visualize, and analyze images that are sent by ScrubCams.


