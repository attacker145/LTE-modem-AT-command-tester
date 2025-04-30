# LTE AT+ Command Tester

## Overview

The **LTE AT+ Command Tester** is a Python-based tool designed to send, receive, and process AT+ commands for testing and configuring LTE modems. This project simplifies interaction with LTE modems by providing a script to automate command execution, parse responses, and log results. It is ideal for developers and engineers working on modem integration or network testing.

### Features

- Send AT+ commands to an LTE modem via a serial connection.
- Parse and display modem responses in a readable format.
- Support for common AT+ commands like `AT+CREG?`, `AT+COPS?`, and `AT+CGDCONT`.
- Configurable serial port settings (e.g., COM port, baud rate).
- Error handling for robust communication with the modem.
- Logging of command interactions for debugging and analysis.

## Requirements

- Python 3.6 or higher  
- Required Python packages:
  - `pyserial` for serial communication  
  - `pillow` for image display  
  - `webbrowser` for web links  
  - `struct`  
  - `binascii`  
  - `socket`  
  - `google`  
  - `pdfplumber`  
  - `subprocess`

Compatible LTE modems are Quectel, Telit, and others, connected via USB or serial interface, Windows, with appropriate serial port drivers.

## Installation

### Clone and Navigate to LTE Modem AT Command Tester
```bash
git clone https://github.com/attacker145/LTE-modem-AT-command-tester.git
cd LTE-modem-AT-command-tester

Set up a virtual environment (recommended, not required):
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:
```bash
pip install pyserial pillow binascii socket google pdfplumber subprocess pillow webbrowser
```

Verify modem connection:
Ensure your LTE modem is connected and drivers are installed.
Identify the modem's serial port (e.g., COM3 on Windows or /dev/ttyUSB0 on Linux).


Usage

Run the script:
python main_lte_ui.py

Select "COM PORT SELECT" for the serial interface.


![com_port_select](https://github.com/user-attachments/assets/c4a966d9-db14-4e90-a7fc-3090e25eec55)

Once the script connects to the serial port, the port settings will be displayed:

![com_port_select_port_number](https://github.com/user-attachments/assets/adda67f3-ec51-4126-b81a-5db020044e4c)

Interact with the modem:

Use the "SINGLE COMMAND" tab to enter any AT+ command (e.g., AT+CREG?) and view the modem's response directly.

![single_command](https://github.com/user-attachments/assets/bd60947b-81f2-48dc-b67c-9f2c68af4bf9)

Use the "DROP DOWN COMMAND" tab to choose from predefined AT+ commands via three drop-down menus. Select a command from any dropdown (e.g., AT+CREG?, AT+COPS?) and click Run to send it to the modem. The modem's response will be displayed immediately.
This tab also has two entry windows to add AT+ commands with descriptions to List A and List B:

![drop_down_command](https://github.com/user-attachments/assets/b0608e93-b9ff-4bfe-9342-41d69096cd6d)

### Run sequence of AT+ commands from a text file 
Syntax: ***command;expected modem response***
```bash
AT+QHTTPCFG="contextid",1;OK
AT+QIACT?;OK
AT+QICSGP=1,1,"soracom.io","","',1;OK
AT+QIACT=1;OK
AT+QIACT?;OK
AT+QHTTPURL=43,80;CONNECT
https://www.jinetinnovations.com/url/post;OK
AT+QHTTPPOST=37,80,80;CONNECT
```


![run_command_file](https://github.com/user-attachments/assets/dd07a33a-34c4-4a70-a222-a7c70ccef0f8)


### LTE Modem Diagnostics page
This page contains buttons programmed with AT+ commands for LTE modem diagnostics.


![diagnostics](https://github.com/user-attachments/assets/c1fd9e66-3060-4e30-8f6a-24c03f0b3d1a)

### PPP Frame Constructor Page

![ppp_frame](https://github.com/user-attachments/assets/9f68ff72-e26c-4235-bc6c-e3e2e9ecd025)
