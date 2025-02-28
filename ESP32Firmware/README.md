# Find My Device ESP32 Firmware

This code enables you to use an ESP32-device as a custom Google Find My Device tracker. Note that the firmware is very experimental.

The firmware works differently to regular Find My Device trackers. It is made to be as simple as possible. It has no Fast Pair support, MAC rotation, advertisement rotation, etc.


## How to use

- Run the Python Script [`main.py`](../main.py) in the parent folder. Follow the instructions of the [README of the parent folder](../README.md).
- When the device list is displayed, press 'r' to register a new ESP32/Zephyr device in your account. Copy the displayed advertisement key.
- Install Visual Studio Code [here](https://code.visualstudio.com/download)
- Go to Visual Studio Code Extensions, search, install and open 'ESP-IDF' by Espressif
- Open the folder containing this README file in Visual Studio Code
- Navigate to the folder main, select the file [`main.c`](main/main.c)
- Edit Line 15, and insert the advertisement key retrieved from the Python Script
- Connect your ESP32 to your system with USB
- On the bottom left of Visual Studio Code, click the 'plug' icon and select your ESP32, it should be named '/dev/tty.usbserial-0001' or similar
- Click the 'Fire' icon to build and flash the firmware
- If asked, use UART as flash method
- After flashing, the ESP32 will restart and start advertising as the Find My Device tracker previously registered


## Known Issues

- You need to run main.c every 4 days to keep receiving location reports from the server. This is because the advertisements have to be "announced" to Google. 
- Might not work with 'fresh' Google accounts: "Your encryption data is locked on your device" is shown if you have never paired a Find My Device tracker with an Android device. Solution: See [README of the parent folder](../README.md).
- You cannot view locations for the ESP32 in the Google Find My Device app. You will need to use the Python script to do so.
- No privacy features such as rotating MAC addresses are implemented
- The firmware was built to receive as many network reports as possible. Therefore, it might consume more power than necessary. To fix this, you can tweak the parameters (TX Power and advertising interval) in [`main.c`](main/main.c)
