# 2018-vision-barebones

This repository provides a barebones base to develop future vision code off of. It includes:

- A V4L2 capture class which supports setting properties such as exposure
- A live video feed web server hosted using Flask
- Main processing loop to extend when details of the game are released
- Comms using ZeroMQ
- Logging configuration
- Basic JSON configuration for all of the above

## Installation and Usage

To install, simply use the included `setup.py` file:

    python setup.py install

Then run it:

    vision2018

## Details of modules

- **__init__.py:** required file for Python packages. We don't use it for anything, so we just leave it blank.
- **__main__.py:** main file containing the `main()` function that is called by `vision2018` when you launch the program. Contains the main processing loop and initialization for everything.
- **capture.py:** used in place of OpenCV's VideoCapture class. Very similar usage. See comments in the file for details about how this works.
- **feed.py:** contains the code needed to start the live video feed web server.
- **config_utils.py:** short utility functions for configuration purposes. Mostly parsing strings.
- **config.json:** JSON configuration for all vision functionality. All future configuration options should be added here.
