LTE AT+ Command Tester
Overview
The LTE AT+ Command Tester is a Python-based tool designed to send, receive, and process AT+ commands for testing and configuring LTE modems. This project simplifies interaction with LTE modems by providing a script to automate command execution, parse responses, and log results. It is ideal for developers and engineers working on modem integration or network testing.
Features

Send AT+ commands to an LTE modem via a serial connection.
Parse and display modem responses in a readable format.
Support for common AT+ commands like AT+CREG?, AT+COPS?, and AT+CGDCONT.
Configurable serial port settings (e.g., COM port, baud rate).
Error handling for robust communication with the modem.
Logging of command interactions for debugging and analysis.

Requirements

Python 3.6 or higher
Required Python packages:
pyserial for serial communication
pillow for image display
webbrowser for web links
struct
binascii
socket
google
pdfplumber
subprocess

A compatible LTE modems are Quectel, Telit, and others, connected via USB or serial interface Windows, with appropriate serial port drivers.

Installation

Clone the repository:
git clone https://github.com/attacker145/LTE-modem-AT-command-tester.git
cd LTE-modem-AT-command-tester


Set up a virtual environment (recommended not required):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install dependencies:
pip install pyserial pillow struct binascii socket google pdfplumber subprocess

Verify modem connection:
Ensure your LTE modem is connected and drivers are installed.
Identify the modem's serial port (e.g., COM3 on Windows or /dev/ttyUSB0 on Linux).



Usage

Run the script:
python main_lte_ui.py

Select "COM PORT SELECT" for the serial interface.

![com_port_select](https://github.com/user-attachments/assets/9f79844a-ed0b-41ed-9671-e695395c093b)

Once the script connects to the serial port, the port settings will be displayed:

![com_port_select_port_number](https://github.com/user-attachments/assets/adda67f3-ec51-4126-b81a-5db020044e4c)

Interact with the modem:

The script will prompt for AT+ commands or execute predefined commands.
Example interaction:Enter an AT+ Command (Press Enter to skip): AT+CREG?
Response: +CREG: 0,1

Use the "SINGLE COMMAND" tab to enter any AT+ command (e.g., AT+CREG?) and view the modem's response directly.

![single_command](https://github.com/user-attachments/assets/bd60947b-81f2-48dc-b67c-9f2c68af4bf9)

View logs:

Command responses are logged to the console and optionally to a file (if implemented).


Example Commands
Here are some common AT+ commands you can test with this tool:

AT: Check modem responsiveness.
AT+CREG?: Query network registration status.
AT+COPS?: Check current operator


![drop_down_command](https://github.com/user-attachments/assets/b0608e93-b9ff-4bfe-9342-41d69096cd6d)
