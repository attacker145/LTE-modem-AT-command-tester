# ui/tab1_serial_setup.py
import tkinter as tk
from tkinter import ttk
import serial.tools.list_ports
import re


class Tab1SerialSetup:
    """
    Handles COM port selection GUI (Tab 1) and basic serial port initialization.
    Moved out from LteInterface to reduce class size.
    """

    def __init__(self, parent_tab, on_port_selected_callback=None):
        self.tab = parent_tab
        self.on_port_selected = on_port_selected_callback
        self.com_ports = []
        self.com_port_var = tk.StringVar()
        self.baud_rate_var = tk.StringVar(value="115200")
        self.parity_var = tk.StringVar(value="None")
        self.ser_settings_text = None

        self._build_ui()
        self.update_com_ports()  # initial scan

    def _build_ui(self):
        tab = self.tab
        bold_font = ("TkDefaultFont", 10, "bold")
        row = 0

        # spacer
        tk.Label(tab, text="").grid(column=0, row=row, padx=5, pady=0, sticky="sw")
        row += 1

        ttk.Label(tab, text="List of COM PORTS", font=bold_font).grid(
            column=0, row=row, padx=5, pady=0, sticky="sw"
        )
        row += 1

        # COM port dropdown
        self.com_port_dropdown = ttk.Combobox(
            tab, textvariable=self.com_port_var, width=60
        )
        self.com_port_dropdown.grid(column=0, row=row, columnspan=2, padx=5, pady=0, sticky="sw")
        self.com_port_dropdown.bind("<<ComboboxSelected>>", self._on_port_selected)

        row += 2  # small gap

        # Labels: Refresh / Baud / Parity
        labels = ["Update COM PORT List", "Set Baud Rate", "Parity"]
        for i, txt in enumerate(labels):
            ttk.Label(tab, text=txt, font=bold_font).grid(
                column=i, row=row, padx=5, pady=0, sticky="sw"
            )

        row += 1

        # Buttons & entries
        tk.Button(tab, text="Refresh COM PORT", command=self.update_com_ports,
                  bd=4, width=20).grid(column=0, row=row, padx=5, pady=0, sticky="sw")

        ttk.Entry(tab, textvariable=self.baud_rate_var, width=19).grid(
            column=1, row=row, padx=5, pady=0, sticky="sw"
        )

        ttk.Entry(tab, textvariable=self.parity_var, width=19).grid(
            column=2, row=row, padx=5, pady=0, sticky="sw"
        )

        row += 2

        # Serial port settings display
        self.ser_settings_text = tk.Text(
            tab, width=80, height=2, font=("Helvetica", 10),
            relief="sunken", state="disabled", wrap="none"
        )
        self.ser_settings_text.grid(column=0, row=row, columnspan=6, rowspan=3, padx=5, pady=0, sticky="nsew")

        # horizontal scrollbar
        hsb = tk.Scrollbar(tab, orient="horizontal")
        hsb.grid(row=row+3, column=0, columnspan=6, sticky="ew")
        self.ser_settings_text.config(xscrollcommand=hsb.set)
        hsb.config(command=self.ser_settings_text.xview)

        # enable momentarily to set initial empty text
        self.ser_settings_text.config(state='normal')
        self.ser_settings_text.delete('1.0', tk.END)
        self.ser_settings_text.insert('1.0', "No port selected")
        self.ser_settings_text.config(state='disabled')

    def update_com_ports(self):
        """Refresh list of available COM ports"""
        ports = serial.tools.list_ports.comports()
        self.com_ports = [str(p) for p in ports]  # or [p.device for p in ports]
        self.com_port_dropdown['values'] = self.com_ports

        if self.com_ports:
            self.com_port_var.set(self.com_ports[0])
            self._on_port_selected(None)  # simulate selection
        else:
            self.com_port_var.set("No ports found")
            self.update_settings_text("No COM ports detected")

    def _on_port_selected(self, event=None):
        port_str = self.com_port_var.get()
        if "No ports" in port_str or not port_str:
            return

        # Extract COMx part
        match = re.search(r'(COM\d+)', port_str)
        com_name = match.group(1) if match else port_str

        baud = self.baud_rate_var.get()
        parity = self.parity_var.get()

        settings = f"Port: {com_name} | Baud: {baud} | Parity: {parity}"
        self.update_settings_text(settings)

        if self.on_port_selected:
            self.on_port_selected(com_name, baud, parity)

    def update_settings_text(self, text: str):
        if not self.ser_settings_text:
            return
        self.ser_settings_text.config(state='normal')
        self.ser_settings_text.delete('1.0', tk.END)
        self.ser_settings_text.insert('1.0', text)
        self.ser_settings_text.config(state='disabled')