import setuptools


setuptools.setup(
    name="scrubcam",
    author="Conservation Technology Lab at the San Diego Zoo Wildlife Alliance",
    description="Code for ScrubCam: Edge-AI-enabled wildlife field camera.",
    packages=setuptools.find_packages(),
    install_required=[
        'pyyaml',
        'picamera',
        'netifaces',
        'rpi.gpio',
        'numpy',
        'opencv-python',
        'imutils',
        'pillow',
        
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
