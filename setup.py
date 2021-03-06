import os
import re

import setuptools


def read(filename):
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
    with open(path, 'r') as f:
        return f.read()


def find_version(text):
    match = re.search(r"^__version__\s*=\s*['\"](.*)['\"]\s*$", text,
                      re.MULTILINE)
    return match.group(1)


AUTHOR = "Conservation Technology Lab at the San Diego Zoo Wildlife Alliance"
DESC = "Code for ScrubCam: Edge-AI-enabled wildlife field camera."

setuptools.setup(
    name='scrubcam',
    description=DESC,
    long_description=read('README.md'),
    license="MIT",
    version=find_version(read('scrubcam/__init__.py')),
    author=AUTHOR,
    packages=['scrubcam'],
    install_requires=[
        'pyyaml',
        'netifaces',
        'numpy',
        'opencv-python==4.5.4.60',
        'imutils',
        'pillow',
        'camml',
    ],
    extras_require={
        'pi': ['dencam',
               'picamera',
               'rpi.gpio',
               'adafruit-circuitpython-ssd1306',
               'adafruit-circuitpython-rfm9x']
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Scientific/Engineering",
    ],
    entry_points={'console_scripts': ["scrubcam=scrubcam.__main__:main"]},
)
