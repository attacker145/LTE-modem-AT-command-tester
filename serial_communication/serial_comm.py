import re
import serial.tools.list_ports
import datetime
import logging
from utils import time_delay
import tkinter as tk

rtn = "\r\n"


class SerialCommunication:
    def __init__(self, com_port_get, com_port_dropdown, com_port_var_tab1, timeout, baud_rate_tab1, parity_tab1, display_comport_settings, displ_modem_response_tab4):
        self.com_port = com_port_get
        self.com_port_str = ""
        self.com_ports = []
        self.assigned_com_port = None
        self.com_port_serial = None  # Store the serial.Serial object
        self.counter = 0
        self.exit = False
        self.com_port_dropdown = com_port_dropdown  # used
        self.get_com_ports()                        # Initialize the drop-down com ports
        self.com_port_var_tab1 = com_port_var_tab1
        self.timeout = timeout
        self.baud_rate_tab1 = baud_rate_tab1
        self.baud = 115200
        self.parity_tab1 = parity_tab1
        self.parity = "N"
        self.display_comport_settings = display_comport_settings
        self.displ_modem_response_tab4 = displ_modem_response_tab4

    def exit_app(self):
        print('exit method called')
        self.exit = True
        quit()
        return

    def get_current_com_port(self):  # Not used
        """
        This function helps to determine the status (open or closed) of a specific COM port based on a
        pre-assigned name (self.com_port). If the assigned port is not found among available ports, it indicates
        the port might not be connected or available.

        If self.com_port is assigned, the function iterates over available COM ports using
        serial.tools.list_ports.comports(). This function returns a list of tuples representing available COM ports,
        typically containing information like device name, description, etc.

        Inside the loop, it compares the device attribute of each port in the list with self.com_port. If there's a
        match, it means the expected COM port is found.

        If a matching port is found:
        It further checks if a serial connection (self.com_port_serial) is already established and open using is_open.
        If the connection is open, it returns a string indicating the COM port name followed by "(Open)".
        If the connection is not open, it returns a string indicating the COM port name followed by "(Closed)".

        If the loop iterates through all available ports and no match is found for self.com_port, it returns a string
        indicating the COM port name followed by "(Not found)".

        If self.com_port is not set at the beginning (meaning no COM port is assigned), the function returns a string
        indicating "No COM port assigned".
        :return:  string
        """
        if self.com_port:
            for port in serial.tools.list_ports.comports():
                if port.device == self.com_port:
                    if self.com_port_serial and self.com_port_serial.is_open:
                        return f"{self.com_port} (Open)"
                    else:
                        return f"{self.com_port} (Closed)"
            return f"{self.com_port} (Not found)"
        else:
            return "No COM port assigned"

    def is_port_open(self):
        return self.com_port.is_open

    def select_and_assign_com_port_from_drop_down(self):

        serial_port = None

        parity_map = {
            "None": serial.PARITY_NONE,
            "Even": serial.PARITY_EVEN,
            "Odd": serial.PARITY_ODD
        }
        self.parity = self.parity_tab1.get()   # "None" "Even" "Odd"
        parity_value = parity_map.get(self.parity, serial.PARITY_NONE)  # Default to NONE if invalid
        print(parity_value)

        self.com_port_str = self.com_port_var_tab1.get()  # Get user selected PORT

        match = re.search(r'COM\d+', str(self.com_port_str))
        if match:
            serial_port = match.group()
        if self.com_port_str:
            try:
                self.baud = int(self.baud_rate_tab1.get())  # Get user selected Baud rate
                self.com_port = serial.Serial(serial_port, self.baud, parity=parity_value, timeout=self.timeout)  # Assign
                settings_text = f"Port: {self.com_port}\n"
                self.display_comport_settings(settings_text)
                print(f"Opened COM port: {serial_port}")
            except serial.SerialException as e:
                print(f"Error opening COM port {self.com_port_str}: {e}")
                self.display_comport_settings(f"Error opening COM port {self.com_port_str}: {e}")
        else:
            print("Select COM PORT from the drop down")
            self.display_comport_settings("Select COM PORT from the drop down")
        # self.display_comport_settings(self.com_port_str)
        return self.baud, self.com_port

    def get_com_ports(self):
        """
        This function retrieves information about available communication ports on the system.
        List of comports for the COM port drop down. Runs on __init__:
        :return:
        """
        # self.com_ports = [port.device for port in serial.tools.list_ports.comports()]
        """
        Returns serial.tools.list_ports_common.ListPortInfo object. ListPortInfo objects contain details like device 
        name, description, and hardware ID.
        """
        self.com_ports = [port for port in serial.tools.list_ports.comports()]
        return self.com_ports

    def update_com_ports(self):
        """
        This function is responsible for updating a dropdown menu
        Update COM ports button. Button control
        :return:
        """
        self.get_com_ports()
        self.com_port_dropdown["values"] = self.com_ports
        for port in self.com_ports:
            match = re.search(r'COM\d+', str(port))
            if match:
                com_port = match.group()
                print(com_port)

    def get_device_info(self):
        self.com_port.write(b"AT+GMI" + rtn.encode())

    def conn_status(self):
        self.com_port.write(b"AT+CEREG?" + rtn.encode())

    def current_config(self):
        self.com_port.write(b"AT&V" + rtn.encode())

    def sim_iccid(self):
        self.com_port.write(b"AT+ICCID" + rtn.encode())

    def at_cops_question(self):
        self.com_port.write(b"AT+COPS?" + rtn.encode())

    def ip_addr(self):
        self.com_port.write(b"AT+CGPADDR=1" + rtn.encode())

    def apn(self):
        self.com_port.write(b"AT+CGDCONT?" + rtn.encode())

    def sig_quality(self):
        self.com_port.write(b"AT+CSQ" + rtn.encode())

    def pdp_context_state(self):
        self.com_port.write(b"AT+CGACT?" + rtn.encode())

    def imsi(self):
        self.com_port.write(b"AT+CIMI" + rtn.encode())

    def send_command(self, command, response="OK"):
        timeout = 40
        self.com_port.write(command.encode() + rtn.encode())
        start_time = datetime.datetime.now()
        elapsed_time = (datetime.datetime.now() - start_time).total_seconds()
        line = str(self.com_port.readline().strip())
        while response not in line:
            line = str(self.com_port.readline().strip())
            if line and line not in ("\r", "\n"):
                print("Rspnse: {}".format(line))
                logging.debug("Rspnse: {}".format(line))
                self.displ_modem_response_tab4.insert(tk.END, line)
                self.displ_modem_response_tab4.see(tk.END)
            else:
                print("Waiting for modem response {} sec...".format(elapsed_time))
                logging.debug("Waiting for modem response {} sec...".format(elapsed_time))
                self.displ_modem_response_tab4.insert(tk.END, "Waiting for modem response {} sec...".format(elapsed_time))
                self.displ_modem_response_tab4.see(tk.END)
            time_delay(1)
            if elapsed_time > timeout:
                return
        return line


if __name__ == '__main__':
    com_port_dropdown = []
    com_port_get = "COM37"
    com_port_var_tab1 = timeout = baud_rate_tab1 = display_comport_settings = parity_tab1 = None
    serial_comm = SerialCommunication(com_port_get, com_port_dropdown, com_port_var_tab1, timeout, baud_rate_tab1, parity_tab1, display_comport_settings)
    ports = serial_comm.get_com_ports()
    # ports = serial_comm.update_com_ports()
    print(ports)


