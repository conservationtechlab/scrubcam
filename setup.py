import setuptools


setuptools.setup(
    name="scrubcam",
    author="Conservation Technology Lab at the San Diego Zoo Wildlife Alliance",
    description="Code for ScrubCam: Edge-AI-enabled field camera.",
    packages=setuptools.find_packages(),
    install_requires=[
        'imutils',
        'screeninfo',
        'pillow',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
