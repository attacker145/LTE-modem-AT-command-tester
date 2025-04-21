LTE AT+ Command Tester
Overview
The LTE AT+ Command Tester is a Python-based tool designed to send, receive, and process AT+ commands for testing and configuring LTE modems. This project simplifies interaction with LTE modems by providing a script to automate command execution, parse responses, and log results,
making it ideal for developers and engineers working on modem integration or network testing.
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

A compatible LTE modem, Quectel, Telit, and other, connected via USB or serial interface
Windows, with appropriate serial port drivers.

Installation

Clone the repository:
git clone https://github.com/<your-username>/LTE-modem-AT-command-tester.git
cd LTE-modem-AT-command-tester


Set up a virtual environment (recommended):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install dependencies:
pip install pyserial pillow struct binascii socket google pdfplumber subprocess

Verify modem connection:

Ensure your LTE modem is connected and drivers are installed.
Identify the modem's serial port (e.g., COM3 on Windows or /dev/ttyUSB0 on Linux).



Usage

Configure the script:

Open main.py (or your main script) and update the serial port and baud rate settings:SERIAL_PORT = "COM3"  # Replace with your modem's port
BAUD_RATE = 115200    # Common baud rate for LTE modems




Run the script:
python main.py


Interact with the modem:

The script will prompt for AT+ commands or execute predefined commands.
Example interaction:Enter an AT+ Command (Press Enter to skip): AT+CREG?
Response: +CREG: 0,1




View logs:

Command responses are logged to the console and optionally to a file (if implemented).



Example Commands
Here are some common AT+ commands you can test with this tool:

AT: Check modem responsiveness.
AT+CREG?: Query network registration status.
AT+COPS?: Check current operator


![drop_down_command](https://github.com/user-attachments/assets/b0608e93-b9ff-4bfe-9342-41d69096cd6d)
