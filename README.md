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

# Setup

This section deserves some attention :-)

# Usage

## On Raspberry Pi 

The core program in the project is `scrubcam.py` which runs on the
Raspberry Pi which is controlling the field device. It accepts a YAML
configuration file as a command line argument. There is an example
config file `./cfgs/config.yaml.example`

You can copy this example file and modify it to your specific purposes
and thus then run ScrubCam on a properly set up system (see Setup
section above for how to set up system) via:

     ./scrubcam.py cfgs/YOUR_CONFIG_FILE.yaml

## On server system 

For monitoring the activity of a ScrubCam there is also a small
server/dashboard program called `scrubhub.py` intended to be run on a
machine on the same network (e.g. back in the lab or on a laptop in
the field). This will soon be deprecated as it is being replaced by a
Plotly-Dash-based server/dashboard.


