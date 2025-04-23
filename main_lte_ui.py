import binascii
import json
import logging
import os
import re
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, Toplevel
from tkinter import ttk
import serial
from serial.tools import list_ports
import webbrowser

from PPP.construct_ppp_frame_with_tcp_headerv02 import create_ppp_frame, parse_tcp_header, extract_ppp_payload
from display_image import DisplayImagesUserInterfaceInit
from file_operations import FileEditorApp, count_bytes_in_file, process_files
from links import quectel_forums, qbg95, tc1wwg, lte_books
from resources.process_modem_responses import ModemResponses
from search_pdf.search_books import find_and_open_first_match
from tool_tip import Tooltip
from update_json import update_json
from utils import parse_csq_response, parse_servinfo_response, parse_at_atrfsts, Timer
from serial_communication.serial_comm import SerialCommunication

rtn = "\r\n"
ports = []


def create_entry(root, textvar, default_text, row, column):
    entry = tk.Entry(root, textvariable=textvar, bg='#33FFAA', bd=4, highlightcolor='#33FF44',
                     font=("Helvetica", 10), width=25)
    textvar.set(default_text)
    entry.grid(column=column, row=row, padx=5, pady=0, sticky="nw")


def create_checkbutton(root, text, variable, row, column, command=None):
    checkbutton = tk.Checkbutton(root, text=text, bg='#d9d9de', variable=variable, onvalue=1,
                                 offvalue=0, command=command)
    checkbutton.grid(column=column, row=row, padx=0, pady=0)


def exit_program():
    print("Exiting the script...")  # This will now print reliably
    sys.exit()


def load_descriptions(filepath="resources/list_b_commands.json"):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Description file '{filepath}' not found. Using default descriptions.")
        return {}  # Or provide some default descriptions


def remove_comment(line):
    return line.split('#')[0].strip()


def format_time(seconds):
    seconds = int(seconds)
    minutes = seconds // 60
    hours = minutes // 60
    return f"{hours:02d}:{minutes % 60:02d}:{seconds % 60:02d}"


class LteInterface(DisplayImagesUserInterfaceInit):
    def __init__(self, top_level, input_file):
        super().__init__()
        # Initialize SerialCommunication with required parameters
        global ports
        self.top_level = top_level
        self.tab_control = ttk.Notebook(self.top_level)
        self.stop, self.disable, self.is_running = [False] * 3
        self.input_file = input_file
        self.at_command = self.at_command_tab5 = self.com_port_str = ""
        self.com_ports = []
        self.assigned_com_port, self.com_port_serial, self.serial_port, self.com_port, self.line_string, self.log_file_path = [None] * 6
        self.timeout = 1
        self.baud = 115200
        self.start_time = self.elapsed_time = self.line_number = 0
        self.command = []
        self.expected_response = []
        self.get_com_ports()
        self.timer = Timer()
        # ---------------------- Create Tabs -----------------------------------------------------------------
        tab_count = 6  # The number of tabs
        tabs = [ttk.Frame(self.tab_control) for _ in range(tab_count)]
        self.tab1, self.tab2, self.tab3, self.tab4, self.tab5, self.tab6 = tabs
        tab_info = [('COM PORT SELECT', self.tab1), ('SINGLE COMMAND', self.tab2), ('DROP DOWN COMMAND', self.tab3),
                    ('RUN COMMAND FILE', self.tab4), ("DIAGNOSTICS", self.tab5), ("PPP Frame", self.tab6)]
        for text, tab in tab_info:
            self.tab_control.add(tab, text=text)
        self.tab_control.pack(expand=1, fill="both")

        # ********************** Tab1 SERIAL COMM *******************************************************************
        # COM PORT Section
        row = 0  # ---- Blank line1
        tk.Label(self.tab1, text="").grid(column=0, row=row, padx=5, pady=0, sticky="sw")

        bold_font = ("TkDefaultFont", 10, "bold")  # Specify the font here

        row = 1  # ---- Drop down label
        labels = ["List of COM PORTS"]
        for i, label in enumerate(labels):
            ttk.Label(self.tab1, text=label, font=bold_font).grid(column=i, row=row, padx=5, pady=0, sticky="sw")

        row = 2  # -- +1 Row
        column = 0  # COM PORT drop down
        self.com_port_var_tab1 = tk.StringVar()
        self.com_port_dropdown = ttk.Combobox(self.tab1, textvariable=self.com_port_var_tab1, values=self.com_ports,
                                              width=60)
        self.com_port_dropdown.grid(column=column, row=row, columnspan=2, padx=5, pady=0, sticky="sw")
        column += 2  # Button - Select COM Port

        row = 3  # ---- Blank line
        tk.Label(self.tab1, text="").grid(column=0, row=row, padx=5, pady=0, sticky="sw")
        row = 4  # -- +1 Row
        labels = ["Update COM PORT List", "Set Baud Rate", "Parity"]
        for i, label in enumerate(labels):
            ttk.Label(self.tab1, text=label, font=bold_font).grid(column=i, row=row, padx=5, pady=0, sticky="sw")
        row = 5  # -- +1 Row
        column = 0  # BTN: Refresh COM PORT
        self.update_button = tk.Button(self.tab1, text="Refresh COM PORT", command=self.update_com_ports, bd=4,
                                       width=20)
        self.update_button.grid(column=column, row=row, padx=5, pady=0, sticky="sw")

        column += 1  # Baud rate
        self.baud_rate_tab1 = tk.StringVar()
        self.baud_rate_tab1.set("115200")
        self.baud_rate_tab1 = tk.Entry(self.tab1, textvariable=self.baud_rate_tab1, bg='#33FFAA', bd=4, width=19,
                                       highlightcolor='#33FF44',
                                       font=("Helvetica", 10))
        self.baud_rate_tab1.grid(column=column, row=row, columnspan=1, rowspan=1, padx=5, pady=0, sticky="sw")

        column += 1  # Parity
        self.parity_tab1 = tk.StringVar()
        self.parity_tab1.set("None")
        self.parity_tab1 = tk.Entry(self.tab1, textvariable=self.parity_tab1, bg='#33FFAA', bd=4, width=19,
                                    highlightcolor='#33FF44',
                                    font=("Helvetica", 10))
        self.parity_tab1.grid(column=column, row=row, columnspan=1, rowspan=1, padx=5, pady=0, sticky="sw")

        row = 6  # ---- Blank line
        tk.Label(self.tab1, text="").grid(column=0, row=row, padx=5, pady=0, sticky="sw")

        row = 7
        column = 0  # ---- Display Modem response Text Entry field
        self.ser_port_settings_tab1 = tk.Text(
            self.tab1,
            width=80,
            height=2,
            font=("Helvetica", 10),
            relief="sunken",
            state="disabled",
            wrap="none"  # Disable automatic line wrapping
        )
        self.ser_port_settings_tab1.grid(column=column, row=row, columnspan=6, rowspan=3, padx=5, pady=0, sticky="nsew")
        self.ser_port_settings_tab1.config(state='normal')
        self.ser_port_settings_tab1.delete('1.0', tk.END)
        self.ser_port_settings_tab1.insert('1.0', "")
        # self.ser_port_settings_tab1.config(state='disabled')
        row += 3  # Scrollbar:
        scrollbar = tk.Scrollbar(self.tab1, orient="horizontal")
        scrollbar.grid(row=row, column=column, columnspan=6, sticky="ew")

        # Connect the scrollbar to the Text widget
        self.ser_port_settings_tab1.config(xscrollcommand=scrollbar.set)
        scrollbar.config(command=self.ser_port_settings_tab1.xview)

        row += 1
        column = 0  # Checkbox: Enable VertexAI prompt
        # self.select_ai = tk.IntVar()
        # create_checkbutton(self.tab4, 'Enable VertexAI prompt', self.select_ai, row, column, self.ai_check_box)
        self.select_ai = tk.BooleanVar()
        self.ai_check_box = tk.Checkbutton(self.tab1, text='Enable VertexAI prompt', font=bold_font,
                                           variable=self.select_ai)
        self.ai_check_box.grid(row=row, column=column)

        column += 1  # Checkbox: Enable Google Search
        self.google_search = tk.BooleanVar()
        self.google_search_check_box = tk.Checkbutton(self.tab1, text='Enable Google Search', font=bold_font,
                                                      variable=self.google_search)
        self.google_search_check_box.grid(row=row, column=column)

        column += 1  # Checkbox: Verb
        self.verb = tk.BooleanVar()
        self.verb_check_box = tk.Checkbutton(self.tab1, text='Response Analysis Printout', font=bold_font, variable=self.verb)
        self.verb_check_box.grid(row=row, column=column)

        column += 2  # Image
        self.panel = ttk.Label(self.tab1, image=self.image_tab1)
        self.panel.image = self.image_tab1
        self.panel.grid(column=column, row=row, columnspan=3, rowspan=3, padx=0, pady=10, sticky="nw")

        # Make the image clickable
        self.website_url = "https://www.jinetinnovations.com/"  # Default URL

        def open_website(event):
            webbrowser.open(self.website_url)
        self.panel.bind("<Button-1>", open_website)

        # Hover functionality (size and cursor)
        def on_enter(event):
            self.panel.configure(image=self.image_hover, cursor="hand2")  # Change to pointing finger
            self.panel.image = self.image_hover

        def on_leave(event):
            self.panel.configure(image=self.image_normal, cursor="arrow")  # Back to default arrow
            self.panel.image = self.image_normal

        self.panel.bind("<Enter>", on_enter)
        self.panel.bind("<Leave>", on_leave)

        # Hover functionality
        """def on_enter(event):
            self.panel.configure(image=self.image_hover)
            self.panel.image = self.image_hover  # Update reference

        def on_leave(event):
            self.panel.configure(image=self.image_normal)
            self.panel.image = self.image_normal  # Update reference

        self.panel.bind("<Enter>", on_enter)
        self.panel.bind("<Leave>", on_leave)"""

        row += 1  # ---- Send Command Button for manual command
        column = 0  # EXIT Button
        tk.Button(self.tab1, text="Exit", command=self.exit_app, bd=4, width=20).grid(column=column, row=row, padx=5,
                                                                                      pady=5, sticky="nw")
        # ********************** Tab2 SINGLE COMMAND ***********************************************************
        row = 0  # ---- Blank line -----------------------------------------------------------------------------
        tk.Label(self.tab2, text="").grid(column=0, row=row, padx=5, pady=0, sticky="sw")

        row += 1  # ---- Labels for Command Entry Filed and LTE Response -------------------------------------- 1
        bold_font = ("TkDefaultFont", 10, "bold")  # Specify the font here
        labels = ["AT+ Command: Enter AT+ Command Below", "LTE Response"]
        for i, label in enumerate(labels):
            if i == 0:
                ttk.Label(self.tab2, text=label, font=bold_font).grid(column=i, row=row, padx=5, pady=0, sticky="sw")
            else:
                ttk.Label(self.tab2, text=label, font=bold_font).grid(column=i + 1, row=row, padx=5, pady=0,
                                                                      sticky="sw")
        row += 1  # --- Enter Command Text Field
        column = 0
        self.enter_command = tk.Text(self.tab2, height=2, width=40, bg='#33FFAA', bd=4,
                                     highlightcolor='#33FF44', font=("Helvetica", 10))
        self.enter_command.insert(tk.END, "AT+CSQ")
        self.enter_command.grid(column=column, row=row, columnspan=2, padx=5, pady=0, sticky="nw")

        column += 2  # ---- Display Modem response field
        row_span = 20
        colum_nspan = 9
        # Display Modem response Text Entry field
        self.displ_modem_response_tab2 = tk.Text(
            self.tab2,
            width=120,
            height=30,
            font=("Helvetica", 10),
            relief="sunken",
            state="normal",  # Set the initial state to 'normal' for editing
            wrap="word"  # Wrap text at word boundaries to fit the width.
        )
        self.displ_modem_response_tab2.grid(column=column, row=row, columnspan=colum_nspan, rowspan=row_span, padx=5, pady=0,
                                            sticky="nsew")

        # Clear and initialize the Text widget content
        self.displ_modem_response_tab2.delete("1.0", tk.END)
        self.displ_modem_response_tab2.insert("1.0", "")
        self.displ_modem_response_tab2.config(state="normal")  # Keep it editable

        # Add vertical scrollbar
        v_scrollbar = tk.Scrollbar(self.tab2, orient="vertical")
        v_scrollbar.grid(row=row, column=column + colum_nspan, rowspan=row_span, sticky="ns")
        # Connect the scrollbar to the Text widget
        self.displ_modem_response_tab2.config(yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=self.displ_modem_response_tab2.yview)

        row += row_span  # Move to the next row

        # Add horizontal scrollbar
        scrollbar = tk.Scrollbar(self.tab2, orient="horizontal")
        scrollbar.grid(row=row, column=column, columnspan=colum_nspan, sticky="ew")
        # Connect the scrollbar to the Text widget
        self.displ_modem_response_tab2.config(xscrollcommand=scrollbar.set)
        scrollbar.config(command=self.displ_modem_response_tab2.xview)

        column = 0  # BTN: Send LTE Command
        tk.Button(self.tab2, text="Send LTE Command", command=self.send_at_command, bd=4,
                  width=20).grid(column=column, row=3, padx=5, pady=0, sticky="nw")

        row += 1  # ---- Send Command Button for manual command
        column = 0  # EXIT Button
        tk.Button(self.tab2, text="Exit", command=self.exit_app, bd=4, width=20).grid(column=column, row=row, padx=5,
                                                                                      pady=5, sticky="nw")
        column += 2  # ---- Button Save LTE Response
        tk.Button(self.tab2, text="Save LTE Response", command=self.save_lte_resp_to_file, bd=4,
                  width=20).grid(column=column, row=row, padx=2, pady=5, sticky="nw")
        column += 1  # ---- Display Note Field
        self.note_tab2 = tk.Label(self.tab2, text="", fg="Blue", width=40, font=("Helvetica", 10),
                                  relief='sunken')
        self.note_tab2.grid(column=column, row=row, columnspan=2, rowspan=1, padx=5, pady=10, sticky="nw")

        # ********************** Tab3 DROP DOWN COMMAND *****************************************************
        row = 0  # ---- Blank lines                                                                         R0
        tk.Label(self.tab3, text="").grid(column=0, row=row, padx=5, pady=0, sticky="ew")
        # ------------------------------LIST A---------------------------------------------------------
        row += 1  # --- Labels for Send LTE Command button and Drop down List of Commands                   R1
        labels = ["Run List A Command", "List A of AT+ Commands"]
        for i, label in enumerate(labels):
            ttk.Label(self.tab3, text=label, font=bold_font).grid(column=i, row=row, padx=5, pady=0, sticky="sw")

        row += 1  # --- BTN: Run                                                                            R2
        column = 0
        tk.Button(self.tab3, text="Run", command=self.send_at_command_drop_down,
                  bd=4, width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")  # image=self.send_img
        column += 1  # --- Drop down field List of Commands
        self.selected_option_list_a = tk.StringVar()
        self.selected_option_list_a.set("AT+CSQ")  # Default selected option

        def on_combobox_change_lista(event):
            selected_m1 = self.selected_option_list_a.get()
            tooltip_m1.text = descriptions_list_a.get(selected_m1, "No description available")

        descriptions_list_a = load_descriptions("resources/list_a_commands.json")  # Load from JSON file
        self.selected_option_list_a = tk.StringVar()
        self.selected_option_list_a.set("AT+CSQ")  # Default selected option CAT1
        self.dropdown_cat_list_a = ttk.Combobox(self.tab3, textvariable=self.selected_option_list_a,
                                                values=list(descriptions_list_a.keys()),
                                                width=10, height=15)
        self.dropdown_cat_list_a.grid(column=column, row=row, columnspan=2, rowspan=1, padx=7, pady=0, sticky="nsew")
        self.dropdown_cat_list_a.bind("<<ComboboxSelected>>", on_combobox_change_lista)

        tooltip_m1 = Tooltip(self.dropdown_cat_list_a, text=descriptions_list_a["AT+CSQ"])
        self.dropdown_cat_list_a.bind("<Enter>", tooltip_m1.show_tooltip)
        self.dropdown_cat_list_a.bind("<Leave>", tooltip_m1.hide_tooltip)
        # --------------------------------LIST B----------------------------------------------------------
        row += 1  # --- Labels for Send LTE Command button and Drop down List of Commands
        labels = ["Run List B Command", "List B of AT+ Commands"]
        for i, label in enumerate(labels):
            ttk.Label(self.tab3, text=label, font=bold_font).grid(column=i, row=row, padx=5, pady=0, sticky="sw")

        row += 1  # --- Button Send LTE command CAT1
        column = 0
        tk.Button(self.tab3, text="Run", command=self.send_at_command_drop_down_cat1,
                  bd=4, width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")  # image=self.send_img
        column += 1  # --- Drop down field List of Commands

        def on_combobox_change(event):
            selected = self.selected_option_cat1.get()
            tooltip.text = descriptions.get(selected, "No description available")

        descriptions = load_descriptions()  # Load from JSON file
        self.selected_option_cat1 = tk.StringVar()
        self.selected_option_cat1.set("AT+CSQ")  # Default selected option CAT1
        self.dropdown_cat_list_a = ttk.Combobox(self.tab3, textvariable=self.selected_option_cat1,
                                                values=list(descriptions.keys()),
                                                width=10, height=15)
        self.dropdown_cat_list_a.grid(column=column, row=row, columnspan=2, rowspan=1, padx=7, pady=0, sticky="nsew")
        self.dropdown_cat_list_a.bind("<<ComboboxSelected>>", on_combobox_change)

        tooltip = Tooltip(self.dropdown_cat_list_a, text=descriptions["AT+CSQ"])
        self.dropdown_cat_list_a.bind("<Enter>", tooltip.show_tooltip)
        self.dropdown_cat_list_a.bind("<Leave>", tooltip.hide_tooltip)
        # ------------------------------LIST C---------------------------------------------------------
        row += 1  # --- Labels for Send LTE Command button and Drop down List of Commands                   R1
        labels = ["Run List C Command", "List C of AT+ Commands"]
        for i, label in enumerate(labels):
            ttk.Label(self.tab3, text=label, font=bold_font).grid(column=i, row=row, padx=5, pady=0, sticky="sw")

        row += 1  # --- BTN: Run                                                                            R2
        column = 0
        tk.Button(self.tab3, text="Run", command=self.send_at_command_drop_down_list_c,
                  bd=4, width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")  # image=self.send_img
        column += 1  # --- Drop down field List of Commands
        self.selected_option_list_c = tk.StringVar()
        self.selected_option_list_c.set("AT+CSQ")  # Default selected option

        def on_combobox_change_lista(event):
            selected_c = self.selected_option_list_c.get()
            tooltip_c.text = descriptions_list_c.get(selected_c, "No description available")

        descriptions_list_c = load_descriptions("resources/list_c_commands.json")  # Load from JSON file
        self.selected_option_list_c = tk.StringVar()
        self.selected_option_list_c.set("AT+CSQ")  # Default selected option CAT1
        self.dropdown_cat_list_c = ttk.Combobox(self.tab3, textvariable=self.selected_option_list_c,
                                                values=list(descriptions_list_c.keys()),
                                                width=10, height=15)
        self.dropdown_cat_list_c.grid(column=column, row=row, columnspan=2, rowspan=1, padx=7, pady=0, sticky="nsew")
        self.dropdown_cat_list_c.bind("<<ComboboxSelected>>", on_combobox_change_lista)

        tooltip_c = Tooltip(self.dropdown_cat_list_c, text=descriptions_list_a["AT+CSQ"])
        self.dropdown_cat_list_c.bind("<Enter>", tooltip_c.show_tooltip)
        self.dropdown_cat_list_c.bind("<Leave>", tooltip_c.hide_tooltip)
        # ---------------------------------------------------------------------------------------------
        row = 1  # ---- Display Modem response field
        column += 2  # ---- Display Modem response Text Entry field

        tk.Label(self.tab3, text="Modem Response",
                 font=bold_font).grid(column=column, row=row, padx=5, pady=0, columnspan=1, sticky="sw")

        row += 1

        # Display Modem response Text Entry field
        row_span = 20
        colum_nspan_tab3 = 6
        self.displ_modem_response_tab3 = tk.Text(
            self.tab3,
            width=80,
            height=25,
            font=("Helvetica", 10),
            relief="sunken",
            state="normal",  # Set the initial state to 'normal' for editing
            wrap="word"  # Wrap text at word boundaries to fit the width.
        )
        self.displ_modem_response_tab3.grid(column=column, row=row, columnspan=colum_nspan_tab3, rowspan=row_span, padx=5, pady=5,
                                            sticky="nsew")

        # Clear and initialize the Text widget content
        self.displ_modem_response_tab3.delete("1.0", tk.END)
        self.displ_modem_response_tab3.insert("1.0", "")
        self.displ_modem_response_tab3.config(state="normal")  # Keep it editable

        # Add vertical scrollbar
        v_scrollbar = tk.Scrollbar(self.tab3, orient="vertical")
        v_scrollbar.grid(row=row, column=column + colum_nspan_tab3, rowspan=row_span, sticky="ns")
        # Connect the scrollbar to the Text widget
        self.displ_modem_response_tab3.config(yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=self.displ_modem_response_tab3.yview)

        row += row_span  # Move to the next row

        # Add horizontal scrollbar
        scrollbar = tk.Scrollbar(self.tab3, orient="horizontal")
        scrollbar.grid(row=row, column=column, columnspan=colum_nspan_tab3, sticky="ew")
        # Connect the scrollbar to the Text widget
        self.displ_modem_response_tab3.config(xscrollcommand=scrollbar.set)
        scrollbar.config(command=self.displ_modem_response_tab3.xview)

        row = 7
        column = 0  # Note
        self.note_tab3 = tk.Label(self.tab3, text="Note", fg="Blue", font=("Helvetica", 10), relief='sunken', width=10)
        self.note_tab3.grid(column=column, row=row, columnspan=3, rowspan=1, padx=5, pady=20, sticky="nsew")

        column = 0
        row = 8
        tk.Button(self.tab3, text="Exit", command=self.exit_app, bd=4, width=20).grid(column=column, row=row, padx=5,
                                                                                      pady=0, sticky="sw")
        column += 1
        self.clock_display = tk.Label(self.tab3, text="", fg="Blue", width=20, font=("Helvetica", 10), relief='sunken')
        self.clock_display.grid(column=column, row=row, columnspan=1, rowspan=1, padx=5, pady=0, sticky="sw")

        row += row_span
        column = 0
        tk.Label(self.tab3, text="",
                 font=bold_font).grid(column=column, row=row, padx=5, pady=0, columnspan=1, sticky="sw")

        row += 1
        column = 0
        tk.Label(self.tab3, text="Add New AT+ Command to List A",
                 font=bold_font).grid(column=column, row=row, padx=5, pady=0, columnspan=2, sticky="sw")

        tk.Label(self.tab3, text="Add New Command Description to List A",
                 font=bold_font).grid(column=column + 2, row=row, padx=5, pady=0, columnspan=1, sticky="sw")

        row += 1  # Enter AT+ Command entry field
        column = 0
        self.entry_key_list_a = tk.Text(self.tab3, height=1, width=20, bg='#33FFAA', bd=4, highlightcolor='#33FF44',
                                        font=("Helvetica", 10))
        self.entry_key_list_a.insert(tk.END, "")
        self.entry_key_list_a.grid(column=column, row=row, columnspan=2, padx=5, pady=0, sticky="nsew")

        column += 2  # Enter Command Description entry field
        self.entry_value_list_a = tk.Text(self.tab3, height=1, width=40, bg='#33FFAA', bd=4, highlightcolor='#33FF44',
                                          font=("Helvetica", 10))
        self.entry_value_list_a.insert(tk.END, "")
        self.entry_value_list_a.grid(column=column, row=row, columnspan=2, padx=5, pady=0, sticky="nsew")

        column += 2
        tk.Button(self.tab3, text="Add AT+ Command", command=self.add_at_command_list_a, bd=4, width=20).grid(
            column=column,
            row=row, padx=5,
            pady=0, sticky="sw")

        row += 1
        column = 0
        tk.Label(self.tab3, text="Add New AT+ Command to List B",
                 font=bold_font).grid(column=column, row=row, padx=5, pady=0, columnspan=2, sticky="sw")

        tk.Label(self.tab3, text="Add New Command Description to List B",
                 font=bold_font).grid(column=column + 2, row=row, padx=5, pady=0, columnspan=1, sticky="sw")

        row += 1
        column = 0
        self.entry_key_list_b = tk.Text(self.tab3, height=1, width=20, bg='#33FFAA', bd=4, highlightcolor='#33FF44',
                                        font=("Helvetica", 10))
        self.entry_key_list_b.insert(tk.END, "")
        self.entry_key_list_b.grid(column=column, row=row, columnspan=2, padx=5, pady=0, sticky="nsew")

        column += 2  # Enter Command Description entry field
        self.entry_value_list_b = tk.Text(self.tab3, height=1, width=40, bg='#33FFAA', bd=4, highlightcolor='#33FF44',
                                          font=("Helvetica", 10))
        self.entry_value_list_b.insert(tk.END, "")
        self.entry_value_list_b.grid(column=column, row=row, columnspan=2, padx=5, pady=0, sticky="nsew")
        column += 2
        tk.Button(self.tab3, text="Add AT+ Command", command=self.add_at_command_list_b, bd=4, width=20).grid(
            column=column,
            row=row, padx=5,
            pady=0, sticky="sw")

        # ********************** Tab4 RUN COMMAND FILE****************************************************************
        row = 0  # ----
        bold_font = ("TkDefaultFont", 10, "bold")  # Specify the font here
        # Labels
        tk.Label(self.tab4, text="Select AT+ Command File",
                 font=bold_font).grid(column=0, row=row, padx=5, pady=0, columnspan=1, sticky="sw")

        tk.Label(self.tab4, text="Selected File Name:",
                 font=bold_font).grid(column=1, row=row, padx=5, pady=0, columnspan=1, sticky="sw")

        """tk.Label(self.tab4, text="Create/Open AT+ File To Edit",
                 font=bold_font).grid(column=5, row=row, padx=5, pady=0, columnspan=1, sticky="sw")"""

        row += 1  # ---- BTN: Select AT+ File To Run
        column = 0  # ---- BTN: Select AT+ File To Run
        tk.Button(self.tab4, text="Select AT+ File To Run", command=self.select_at_command_file_run, bd=4, width=10). \
            grid(column=column, row=row, padx=5, pady=0, columnspan=1, sticky="nsew")

        column += 1  # ---- Entry Field: Display Filename "support_files/LTE_seq_files/BG95.txt"
        self.file_name = tk.Label(self.tab4, text="", fg="Blue", width=50, font=("Helvetica", 10), relief='sunken')
        self.file_name.grid(column=column, row=row, columnspan=5, rowspan=1, padx=0, pady=5, sticky="nsew")

        column += 5  # ---- BTN: Edit/Create File
        tk.Button(self.tab4, text="Edit/Create File", command=self.open_file, bd=4, width=10). \
            grid(column=column, row=row, padx=5, pady=0, columnspan=1, sticky="nsew")

        row += 1  # ----BTN: Run Next Command
        bold_font = ("TkDefaultFont", 10, "bold")  # Specify the font here
        tk.Label(self.tab4, text="Run Next Command",
                 font=bold_font).grid(column=0, row=row, padx=5, pady=5, columnspan=1, sticky="sw")

        row += 1
        column = 0  # --- BTN: Next AT+ Command
        self.apply_button = tk.Button(self.tab4, text="Run AT+ Command", command=self.send_at_commands_from_file, bd=4,
                                      width=10)
        self.apply_button.grid(column=column, row=row, padx=5, pady=0, columnspan=1, sticky="nsew")

        column += 1  # --- Entry Field: Sent AT+ command
        self.display_sent_messages = tk.Label(self.tab4, text="Sent AT+ command", fg="Blue", width=50,
                                              font=("Helvetica", 10), relief='sunken')
        self.display_sent_messages.grid(column=column, row=row, columnspan=5, rowspan=1, padx=0, pady=5, sticky="nsew")

        column += 5  # --- BTN: Restart Button
        tk.Button(self.tab4, text="Restart", command=self.restart_commands, bd=4, width=10). \
            grid(column=column, row=row, padx=5, pady=0, columnspan=1, sticky="nsew")

        column += 1  # --- Entry field for the start line
        self.start_line = tk.Text(self.tab4, height=1, width=10, bg='#33FFAA', bd=4, highlightcolor='#33FF44',
                                  font=("Helvetica", 10))
        self.start_line.insert(tk.END, "0")
        self.start_line.grid(column=column, row=row, columnspan=1, sticky="nsew", padx=0, pady=0)

        row += 1
        column = 0  # Note
        self.note_tab4 = tk.Label(self.tab4, text="Note", fg="Blue", font=("Helvetica", 10), relief='sunken', width=10)
        self.note_tab4.grid(column=column, row=row, columnspan=3, rowspan=1, padx=5, pady=20, sticky="nsew")

        row += 1
        tk.Label(self.tab4, text="File Contents",
                 font=bold_font).grid(column=0, row=row, padx=5, pady=0, columnspan=1, sticky="sw")
        tk.Label(self.tab4, text="Modem Response:",
                 font=bold_font).grid(column=6, row=row, padx=5, pady=0, columnspan=1, sticky="sw")

        # Display File contents TAB4
        row += 1
        column = 0
        row_span = 15
        column_span = 5
        self.displ_file_tab4 = tk.Text(
            self.tab4,
            height=15,
            width=20,
            font=("Helvetica", 10),
            relief="sunken",
            state="normal",  # Set the initial state to 'normal' for editing
            wrap="word"  # Wrap text at word boundaries to fit the width.
        )
        self.displ_file_tab4.grid(column=column, row=row, columnspan=column_span, rowspan=row_span, padx=5, pady=10,
                                  sticky="nsew")

        # Clear and initialize the Text widget content; Display File contents
        self.displ_file_tab4.delete("1.0", tk.END)
        self.displ_file_tab4.insert("1.0", "No File Selected...")
        self.displ_file_tab4.config(state="normal")  # Keep it editable

        # Add vertical scrollbar; Display File contents
        v_scrollbar = tk.Scrollbar(self.tab4, orient="vertical")
        v_scrollbar.grid(row=row, column=column + column_span, rowspan=row_span, sticky="wns", pady=20)
        # Connect the scrollbar to the Text widget
        self.displ_file_tab4.config(yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=self.displ_file_tab4.yview)

        row += row_span  # Move to the next row
        # Add horizontal scrollbar
        scrollbar = tk.Scrollbar(self.tab4, orient="horizontal")
        scrollbar.grid(row=row, column=column, columnspan=column_span, sticky="ew")
        # Connect the scrollbar to the Text widget
        self.displ_file_tab4.config(xscrollcommand=scrollbar.set)
        scrollbar.config(command=self.displ_file_tab4.xview)

        # Display Modem response Text Entry field TAB4
        column = column_span + 1
        row = 6
        self.displ_modem_response_tab4 = tk.Text(
            self.tab4,
            height=15,
            width=80,
            font=("Helvetica", 10),
            relief="sunken",
            state="normal",  # Set the initial state to 'normal' for editing
            wrap="word"  # Wrap text at word boundaries to fit the width.
        )
        self.displ_modem_response_tab4.grid(column=column, row=row, columnspan=6, rowspan=row_span, padx=5, pady=10,
                                            sticky="nsew")

        # Clear and initialize the Text widget content
        self.displ_modem_response_tab4.delete("1.0", tk.END)
        self.displ_modem_response_tab4.insert("1.0", "")
        self.displ_modem_response_tab4.config(state="normal")  # Keep it editable

        # Add vertical scrollbar
        v_scrollbar = tk.Scrollbar(self.tab4, orient="vertical")
        v_scrollbar.grid(row=row, column=column + 7, rowspan=row_span, sticky="wns", pady=20)
        # Connect the scrollbar to the Text widget
        self.displ_modem_response_tab4.config(yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=self.displ_modem_response_tab4.yview)

        row += row_span  # Move to the next row
        # Add horizontal scrollbar
        scrollbar = tk.Scrollbar(self.tab4, orient="horizontal")
        scrollbar.grid(row=row, column=column, columnspan=6, sticky="ew")
        # Connect the scrollbar to the Text widget
        self.displ_modem_response_tab4.config(xscrollcommand=scrollbar.set)
        scrollbar.config(command=self.displ_modem_response_tab4.xview)

        row += 1
        column = 0
        tk.Button(self.tab4, text="Exit", command=self.exit_app, bd=4, width=10).grid(column=column, row=row, padx=5,
                                                                                      pady=20, sticky="nsew")
        column += 1  # Field: Data file location
        self.input_log_file_path = tk.Text(self.tab4, height=1, width=10, bg='#33FFAA', bd=4, highlightcolor='#33FF44',
                                           font=("Helvetica", 10))
        self.input_log_file_path.insert(tk.END, "logs/rsvp.txt")
        self.input_log_file_path.grid(column=column, row=row, columnspan=3, padx=5, pady=10, sticky="ew")
        print(self.input_log_file_path.get("1.0", "end-1c"))

        column += 3  # BTN: Append Data
        tk.Button(self.tab4, text="Append Data", command=self.append_data_to_post_req, bd=4, width=10).grid(
            column=column, row=row, padx=5, pady=20, sticky="nsew")

        # ******************** Initialize Serial Communication *************************************************
        self.serial_comm = SerialCommunication(
            com_port_get=self.com_port,
            com_port_dropdown=self.com_port_dropdown,
            com_port_var_tab1=self.com_port_var_tab1,
            timeout=1,
            baud_rate_tab1=self.baud_rate_tab1,
            parity_tab1=self.parity_tab1,
            display_comport_settings=self.display_comport_settings,
            displ_modem_response_tab4=self.displ_modem_response_tab4
        )
        # ********************** Tab5 DISPLAY FILE****************************************************************
        row = 0  # ---- Blank lines Tab5
        tk.Label(self.tab5, text="").grid(column=0, row=row, padx=5, pady=0, sticky="ew")
        row += 1
        column = 0  # BTN: Get Device Info
        tk.Button(self.tab5, text="Manufacturer ID", command=self.serial_comm.get_device_info, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")
        column += 1  # BTN: Get Device Info
        tk.Button(self.tab5, text="Conn Status", command=self.serial_comm.conn_status, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")
        column += 1  # BTN: Current Config
        tk.Button(self.tab5, text="Current Config", command=self.serial_comm.current_config, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")

        row += 1    # BTN: SIM CARD CCID Tab5
        column = 0
        tk.Button(self.tab5, text="SIM CARD CCID", command=self.serial_comm.sim_iccid, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")
        column += 1  # BTN: AT+COPS?
        tk.Button(self.tab5, text="MT Network", command=self.serial_comm.at_cops_question, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")
        column += 1  # BTN: AT+CGPADDR=1
        tk.Button(self.tab5, text="IP address", command=self.serial_comm.ip_addr, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")
        row += 1
        column = 0
        tk.Button(self.tab5, text="Read APN", command=self.serial_comm.apn, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")
        column += 1  # BTN: AT+CSQ
        tk.Button(self.tab5, text="Sig Quality (CSQ)", command=self.serial_comm.sig_quality, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")

        column += 1  # BTN: AT+CGACT?
        tk.Button(self.tab5, text="PDP Context State", command=self.serial_comm.pdp_context_state, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")

        row += 1
        column = 0
        tk.Button(self.tab5, text="Read IMSI", command=self.serial_comm.imsi, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")
        column += 1  # BTN: AT+CGACT?
        tk.Button(self.tab5, text="SIM state", command=self.serial_comm.cpin, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")

        row += 1
        column = 0
        self.enter_command_tab5 = tk.Text(self.tab5, height=2, width=40, bg='#33FFAA', bd=4, highlightcolor='#33FF44', font=("Helvetica", 10))
        self.enter_command_tab5.insert(tk.END, "AT+CSQ")
        self.enter_command_tab5.grid(column=column, row=row, columnspan=2, padx=5, pady=0, sticky="ew")
        row += 1
        column = 0  # BTN: Send LTE Command
        tk.Button(self.tab5, text="Send LTE Command", command=self.send_at_command_tab5, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")

        row += 1
        column = 0
        tk.Button(self.tab5, text="Exit", command=self.exit_app, bd=4, width=10).grid(column=column, row=row, padx=5,
                                                                                      pady=0, sticky="ew")

        column += 5
        row = 0
        self.displ_modem_response_tab5 = tk.Text(
            self.tab5,
            height=30,
            width=80,
            font=("Helvetica", 10),
            relief="sunken",
            state="normal",  # Set the initial state to 'normal' for editing
            wrap="word"  # Wrap text at word boundaries to fit the width.
        )
        self.displ_modem_response_tab5.grid(column=column, row=row, columnspan=6, rowspan=row_span, padx=5, pady=10,
                                            sticky="nsew")

        # Clear and initialize the Text widget content
        self.displ_modem_response_tab5.delete("1.0", tk.END)
        self.displ_modem_response_tab5.insert("1.0", "")
        self.displ_modem_response_tab5.config(state="normal")  # Keep it editable

        # Add vertical scrollbar
        v_scrollbar = tk.Scrollbar(self.tab5, orient="vertical")
        v_scrollbar.grid(row=row, column=column + 7, rowspan=row_span, sticky="wns", pady=20)
        # Connect the scrollbar to the Text widget
        self.displ_modem_response_tab5.config(yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=self.displ_modem_response_tab5.yview)

        row += row_span  # Move to the next row
        # Add horizontal scrollbar
        scrollbar = tk.Scrollbar(self.tab5, orient="horizontal")
        scrollbar.grid(row=row, column=column, columnspan=6, sticky="ew")
        # Connect the scrollbar to the Text widget
        self.displ_modem_response_tab5.config(xscrollcommand=scrollbar.set)
        scrollbar.config(command=self.displ_modem_response_tab5.xview)

        row += 1
        column = 0  # Quectel Forums web link
        style = ttk.Style()
        style.configure("BW.TLabel", foreground="blue")
        link = ttk.Label(self.tab5, text="Quectel Forums", style="BW.TLabel", cursor="hand2")
        link.bind("<Button-1>", quectel_forums)
        link.grid(column=column, row=row, padx=5, pady=0, sticky="nw")

        column += 1  # qbg95 web link
        style = ttk.Style()
        style.configure("BW.TLabel", foreground="blue")
        link = ttk.Label(self.tab5, text="QBG95 Folder", style="BW.TLabel", cursor="hand2")
        link.bind("<Button-1>", qbg95)
        link.grid(column=column, row=row, padx=5, pady=0, sticky="nw")

        column += 1  # qbg95 web link
        style = ttk.Style()
        style.configure("BW.TLabel", foreground="blue")
        link = ttk.Label(self.tab5, text="TC1WWG Folder", style="BW.TLabel", cursor="hand2")
        link.bind("<Button-1>", tc1wwg)
        link.grid(column=column, row=row, padx=5, pady=0, sticky="nw")

        column += 1  # qbg95 web link
        style = ttk.Style()
        style.configure("BW.TLabel", foreground="blue")
        link = ttk.Label(self.tab5, text="Books LTE", style="BW.TLabel", cursor="hand2")
        link.bind("<Button-1>", lte_books)
        link.grid(column=column, row=row, padx=5, pady=0, sticky="nw")

        row += 1  # Field: Search directory for a keyword
        column = 0
        bold_font = ("TkDefaultFont", 10, "bold")  # Specify the font here
        tk.Label(self.tab5, text="Search Directory", font=bold_font).grid(column=column, row=row, padx=5, pady=0, columnspan=1, sticky="sw")
        column += 1  # Field: Search keyword
        bold_font = ("TkDefaultFont", 10, "bold")  # Specify the font here
        tk.Label(self.tab5, text="Keyword", font=bold_font).grid(column=column, row=row, padx=5, pady=0, columnspan=1, sticky="sw")

        row += 1  # Field: Search directory
        column = 0
        self.search_dir = tk.Text(self.tab5, height=1, width=10, bg='#33FFAA', bd=4, highlightcolor='#33FF44', font=("Helvetica", 10))
        self.search_dir.insert(tk.END, r"C:\Users\XXX.XXX\Documents\Github\LTE-UI\search_pdf\CAT-M1")
        self.search_dir.grid(column=column, row=row, columnspan=1, padx=5, pady=0, sticky="ew")
        column += 1
        self.keyword = tk.Text(self.tab5, height=1, width=10, bg='#33FFAA', bd=4, highlightcolor='#33FF44', font=("Helvetica", 10))
        self.keyword.insert(tk.END, "COPS")
        self.keyword.grid(column=1, row=row, columnspan=1, padx=5, pady=0, sticky="ew")
        column += 1  # BTN: AT+CGPADDR=1
        tk.Button(self.tab5, text="Search", command=self.search_directory, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=0, sticky="nw")
        # Define the AT commands and their descriptions
        commands = [
            ("Network registration status", "AT+CREG?"),
            ("APN (Access Point Name)", 'AT+CGDCONT=1,"IP","your.apn.here"'),
            ("Activate the PDP context", "AT+CGACT=1,1"),
            ("Attach to the LTE network", "AT+CGATT=1"),
            ("Check IP address", "AT+CGPADDR=1"),
            ("Verify connection status", "AT+COPS?"),
        ]
        column = 1  # Field: Search keyword
        bold_font = ("TkDefaultFont", 10, "bold")  # Specify the font here
        tk.Label(self.tab5, text="Description", font=bold_font).grid(column=column, row=6, padx=20, pady=0,
                                                                     columnspan=1, sticky="sw")
        column += 1
        tk.Label(self.tab5, text="AT Command", font=bold_font).grid(column=column, row=6, padx=20, pady=0,
                                                                    columnspan=1, sticky="sw")

        # Populate the grid with commands
        for i, (description, command) in enumerate(commands, start=1):
            ttk.Label(self.tab5, text=description).grid(row=i + 6, column=1, padx=20, pady=0, sticky=tk.W)
            ttk.Label(self.tab5, text=command).grid(row=i + 6, column=2, padx=0, pady=0, sticky=tk.W)

        # ********************** Tab6 PPP ****************************************************************
        row = 0  # ---- Blank line1
        tk.Label(self.tab6, text="").grid(column=0, row=row, padx=5, pady=0, sticky="sw")

        row += 1  # --- Enter Command Text Field
        column = 0
        self.enter_string = tk.Text(self.tab6, height=2, width=40, bg='#33FFAA', bd=4, highlightcolor='#33FF44', font=("Helvetica", 10))
        self.enter_string.insert(tk.END, "Hello, PPP!")
        self.enter_string.grid(column=column, row=row, columnspan=2, padx=5, pady=0, sticky="nw")

        row += 1
        column = 0  # BTN: AT+CSQ
        tk.Button(self.tab6, text="Convert", command=self.string_to_ppp, bd=4,
                  width=20).grid(column=column, row=row, padx=5, pady=20, sticky="nw")

        column += 2
        row = 0
        self.displ_modem_response_tab6 = tk.Text(
            self.tab6,
            height=30,
            width=100,
            font=("Helvetica", 10),
            relief="sunken",
            state="normal",  # Set the initial state to 'normal' for editing
            wrap="word"  # Wrap text at word boundaries to fit the width.
        )
        self.displ_modem_response_tab6.grid(column=column, row=row, columnspan=10, rowspan=row_span, padx=5, pady=10,
                                            sticky="nsew")

        # Clear and initialize the Text widget content
        self.displ_modem_response_tab6.delete("1.0", tk.END)
        self.displ_modem_response_tab6.insert("1.0", "")
        self.displ_modem_response_tab6.config(state="normal")  # Keep it editable

        # Add vertical scrollbar
        v_scrollbar = tk.Scrollbar(self.tab6, orient="vertical")
        v_scrollbar.grid(row=row, column=column + 11, rowspan=row_span, sticky="wns", pady=20)
        # Connect the scrollbar to the Text widget
        self.displ_modem_response_tab6.config(yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=self.displ_modem_response_tab6.yview)

        # ******* Read lines from the BG95.txt file ******************************************************
        self.file_name.configure(text=str(self.input_file))
        with open(self.input_file, 'r') as f_in:
            self.lines = [line.strip("\n") for line in f_in.readlines()]
        # ************ Initialize Modem Responses ********************************************************
        self.process_modem_response_call = ModemResponses(
            display_modem_response=self.display_modem_response,
            update_note_tabs=self.update_note_tabs,
            google_search_chk=self.google_search,
            select_ai=self.select_ai,
            verb=self.verb
        )

    def string_to_ppp(self):
        ppp_string = self.enter_string.get("1.0", "end-1c")
        frame = create_ppp_frame(ppp_string)
        print("Generated PPP Frame:", frame)
        self.displ_modem_response_tab6.insert(tk.END, binascii.hexlify(frame).decode('utf-8') + "\n")
        self.displ_modem_response_tab6.see(tk.END)
        fields = parse_tcp_header(frame)
        payload = extract_ppp_payload(frame)
        output = (
            f"Source Port: {fields[0]}\n"
            f"Dest Port: {fields[1]}\n"
            f"Seq Num: {fields[2]}\n"
            f"Ack Num: {fields[3]}\n"
            f"Flags: {fields[5]}\n"
            f"Checksum: {hex(fields[7])}\n"
        )
        self.displ_modem_response_tab6.insert(tk.END, output + "\n" + str(payload) + "\n")
        self.displ_modem_response_tab6.see(tk.END)

    def activate_image_link(self):
        """Programmatically trigger the website opening"""
        webbrowser.open(self.website_url)

    def set_url(self, new_url):
        """Change the URL the image links to"""
        self.website_url = new_url

    def add_at_command_list_a(self):
        """
        Add command and description to list A
        """
        key = self.entry_key_list_a.get("1.0", "end-1c").strip()
        value = self.entry_value_list_a.get("1.0", tk.END).strip()
        update_json("resources/list_a_commands.json", key, value)
        self.entry_key_list_a.delete("1.0", tk.END)
        self.entry_value_list_a.delete("1.0", tk.END)

    def add_at_command_list_b(self):
        """
        Add command and description to list B
        """
        key = self.entry_key_list_b.get("1.0", "end-1c").strip()
        value = self.entry_value_list_b.get("1.0", tk.END).strip()
        update_json("resources/list_b_commands.json", key, value)
        self.entry_key_list_b.delete("1.0", tk.END)
        self.entry_value_list_b.delete("1.0", tk.END)

    def search_directory(self):
        """
        Search directory for a keyword
        """
        books_dir = self.search_dir.get("1.0", "end-1c").strip()
        query = self.keyword.get("1.0", "end-1c").strip()
        if not books_dir:
            print("Error: No directory specified.")
            return
        result = find_and_open_first_match(books_dir, query)
        if not result:
            print("No books found with the requested information.")

    def ai_check_box(self):
        if self.select_ai.get() == 1:
            print("AI Is Selected")
        else:
            print("AI Is Not Selected")

    def google_search_check_box(self):
        if self.google_search.get() == 1:
            print("Google Search Is Enabled")
        else:
            print("Google Search Is Not Enabled")

    def append_data_to_post_req(self):
        self.log_file_path = self.input_log_file_path.get("1.0", "end-1c")
        print(self.log_file_path)
        self.log_file_path = str(self.log_file_path)
        # self.log_file_path = logs/rsvp.txt
        process_files(self.log_file_path, "support_files/command_sequence_files/CAT1.txt",
                      "support_files/command_sequence_files/CAT1_appended.txt")

    def get_file_size(self):
        """
        Not used
        """
        self.log_file_path = self.input_log_file_path.get("1.0", "end-1c")
        print(self.log_file_path)
        self.log_file_path = str(self.log_file_path)
        bytes = count_bytes_in_file(self.log_file_path)
        print("File size {} bytes".format(bytes))

    def update_clock(self):
        """
        Front panel clock
        :return:
        """
        current_time = time.strftime('%H:%M:%S')
        self.clock_display.config(text=current_time)
        root.after(1000, self.update_clock)  # Update every 1000 milliseconds (1 second)

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time() - self.elapsed_time
            """while self.is_running:
                self.elapsed_time = time.time() - self.start_time
                print(format_time(self.elapsed_time))
                time.sleep(1)"""

    def update_timer(self):
        if self.is_running:
            self.elapsed_time = time.time() - self.start_time
            print("MT Time Lapse... {} sec".format(self.elapsed_time))
            self.process_modem_response("MT Time Lapse... {} sec".format(self.elapsed_time))
            # time.sleep(1)

    def stop_timer(self):
        if self.is_running:
            self.is_running = False
            self.elapsed_time = time.time() - self.start_time

    def reset_timer(self):
        self.is_running = False
        self.elapsed_time = 0
        print("Timer reset to 00:00:00")

    def select_at_command_file_run(self):
        """
        Used by "Select File To Run" button. When button is pressed file gets loaded and self.lines gets text
        :return:
        """
        self.input_file = filedialog.askopenfilename(title="Select Input File", filetypes=[("Text Files", "*.txt")])

        if self.input_file:
            self.file_name.configure(text=str(self.input_file))
            with open(self.input_file, 'r') as f_in:
                self.lines = [line.strip("\n") for line in f_in.readlines()]
            # Clear the Text widget before inserting new content
            # self.displ_file_tab5.delete("1.0", tk.END)
            self.displ_file_tab4.delete("1.0", tk.END)

            # Insert file contents into the Text widget
            # self.displ_file_tab5.insert("1.0", "\n".join(self.lines))
            self.displ_file_tab4.insert("1.0", "\n".join(self.lines))

            # Keep the widget editable
            # self.displ_file_tab5.config(state="normal")
            self.displ_file_tab4.config(state="normal")

    def send_at_commands_from_file(self):
        """
        RUN COMMAND FILE
        Send list of commands from selected file. The default file is read in the constructor >>>>>>>SEND>>>>>>>>>>>>>>>
        :return:
        """
        data = ""
        content_length = None
        # Getting commands from the text file
        if self.line_number < len(self.lines):
            line = self.lines[self.line_number]  # Load the next line of the text file
            print(line)
            # Get Command and Response for each line
            line_list = line.split(';')
            print(line_list)
            if len(line_list) > 1:
                self.command = line_list[0]
                self.expected_response = line_list[1]
                print("Command {}".format(self.command))
                print("Expected Response {}".format(self.expected_response))
            else:
                self.command = line
                self.expected_response = None
            self.line_number += 1
            # Sending commands from the text file
            if self.com_port:
                if not self.command.strip().startswith("#"):
                    self.start_timer()  # Timer Start
                if self.command.strip().startswith("#"):  # Skip lines with # at the start and load the next command
                    self.display_sent_messages.configure(text="{}, Line {}".format(self.command, self.line_number))
                    logging.debug("{}, Line #{}".format(self.command, self.line_number))
                    print("{}, Line #{}".format(self.command, self.line_number))
                elif self.command.strip().startswith("AT"):  # Command
                    # line = line.replace('"', '\\"')
                    self.com_port.write(self.command.encode() + rtn.encode())  # Send command + RTN
                    # Update GUI and logs
                    self.display_sent_messages.configure(text="{}, Line {}".format(self.command, self.line_number))
                    logging.debug("{}, Line #{}".format(self.command, self.line_number))
                    print("{}, Line #{}".format(self.command, self.line_number))
                    # Disable the button when reaching the end of the list
                    if self.line_number >= len(self.lines):
                        self.apply_button.configure(state=tk.DISABLED)
                elif self.command.strip() == "+++":
                    self.com_port.write(self.command.encode() + rtn.encode())  # Send command + RTN
                    # Update GUI and logs
                    self.display_sent_messages.configure(text="{}, Line {}".format(self.command, self.line_number))
                    logging.debug("{}, Line #{}".format(self.command, self.line_number))
                    print("{}, Line #{}".format(self.command, self.line_number))
                    # Disable the button when reaching the end of the list
                    if self.line_number >= len(self.lines):
                        self.apply_button.configure(state=tk.DISABLED)
                elif self.command.strip().startswith("http"):
                    self.com_port.write(self.command.encode() + rtn.encode())  # Send command + RTN
                    # Update GUI and logs
                    self.display_sent_messages.configure(text="{}, Line {}".format(self.command, self.line_number))
                    logging.debug("{}, Line #{}".format(self.command, self.line_number))
                    print("{}, Line #{}".format(self.command, self.line_number))
                    self.process_modem_response(self.command)
                    # Disable the button when reaching the end of the list
                    if self.line_number >= len(self.lines):
                        self.apply_button.configure(state=tk.DISABLED)
                else:
                    line = self.lines[self.line_number - 1]
                    line = line + "\r\n"
                    data += line
                    while self.line_number < len(self.lines) and not self.lines[self.line_number].startswith("AT"):  # Send the appended file:  # Send the appended file
                        line = self.lines[self.line_number]
                        if line.lower().startswith("rsvp="):
                            content_length = len(line)
                            print(line + str(content_length))
                        """
                        if line.lower().startswith("content-length:"):
                            if content_length is not None:
                                line = f"Content-Length: {content_length}"
                        """
                        line = line + "\r\n"
                        data += line
                        self.line_number += 1

                    new_data = ""
                    for line in data.splitlines():
                        if line.lower().startswith("content-length:"):
                            if content_length is not None:
                                line = f"Content-Length: {content_length}"
                        new_data += line + "\r\n"  # Or "\n" depending on protocol

                    self.process_modem_response(new_data)

                    print("POST Req below:\n" + new_data)
                    self.com_port.write(new_data.encode())  # Send data + RTN
                    self.com_port.write(b'\r\n')  # Ctrl+M (CR) + Ctrl+J (LF), first newline
                    self.com_port.write(b'\r\n')  # Ctrl+M (CR) + Ctrl+J (LF), second newline
                    self.com_port.write(chr(26).encode())  # Ctrl+Z (SUB character)
            else:
                self.display_sent_messages.configure(text="ERROR: COM PORT NOT SELECTED")
        return

    def restart_commands(self):
        start_line_num = 0
        try:
            start_line_text = self.start_line.get("1.0", "end-1c")

            try:
                start_line_num = int(start_line_text)
                print("Successfully converted to integer:", start_line_num)
            except ValueError:
                try:
                    start_line_num = float(start_line_text)
                    print("Successfully converted to float:", start_line_num)
                except ValueError:
                    print(f"Error: '{start_line_text}' cannot be converted to a number (int or float).")
                    start_line_num = 0  # Or a default value, or raise an exception
                    # ... other error handling ...
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            start_line_text = None  # Or a default value

        # Example usage (after the conversion attempt)
        if self.at_command is not None:
            result = self.at_command * 2  # Example operation
            print("Result:", result)
        else:
            print("Cannot perform calculation because at_command is not a valid number.")

        self.line_number = start_line_num
        self.apply_button.configure(state=tk.NORMAL)

    def display_modem_response(self, read_val):
        # Ensure the message starts on a new line
        new_message = "\r\n\r\n" + read_val

        # Append to each text widget instead of replacing the content
        self.displ_modem_response_tab2.insert(tk.END, new_message)
        self.displ_modem_response_tab3.insert(tk.END, new_message)
        self.displ_modem_response_tab4.insert(tk.END, new_message)
        self.displ_modem_response_tab5.insert(tk.END, new_message)

        # Auto-scroll to the end to show the latest message
        self.displ_modem_response_tab2.see(tk.END)
        self.displ_modem_response_tab3.see(tk.END)
        self.displ_modem_response_tab4.see(tk.END)
        self.displ_modem_response_tab5.see(tk.END)

    def read_modem_response_continuously(self):
        """
        Read modem responses over a serial port continuously <<<<<<<<<<<<<<<<<<<<<<<<<<<<<READ<<<<<<<<<<<<<<<<<<<<<<<<<
        :return:
        """
        while True:
            self.update_clock()
            if self.com_port:
                if self.com_port.is_open:
                    read_val = self.com_port.read(1024)  # Read 1024 byte response
                    read_val = '\n'.join(line for line in read_val.decode('utf-8').splitlines() if line.strip())
                    if read_val:
                        if "ERROR" in read_val:  # To prevent timer display after error is received
                            self.stop_timer()
                            self.reset_timer()
                        print("Modem Response Below:\n" + read_val)
                        read_val = str(parse_csq_response(read_val))  # Extracts RSSI and BER values from the +CSQ response.
                        read_val = str(parse_servinfo_response(read_val))  # #SERVINFO: Combined and parsed message
                        read_val = str(parse_at_atrfsts(read_val))  # #RFSTS Combined and parsed message
                        self.process_modem_response(read_val)  # If there is an error it will be display here
                        if self.expected_response is not None:
                            if str(self.expected_response) in read_val:  # Received the expected response
                                self.stop_timer()
                                self.reset_timer()
                                self.process_modem_response("Done!")
                            else:
                                self.update_timer()
                    else:
                        self.update_timer()
                else:
                    break
            else:
                self.select_and_assign_com_port_from_drop_down_tab1()
                time.sleep(2)
                if self.stop:
                    if self.com_port:
                        if self.com_port.is_open:
                            self.com_port.close()
                            break
            if self.stop:
                if self.com_port:
                    if self.com_port.is_open:
                        self.com_port.close()
                break
        quit()
        """
        print("Stop")
        root.destroy()  # Correct way to close the window
        root.after(0, exit_program)  # Schedule exit_program to run after 0ms
        quit()
        print("Exiting the script...")
        sys.exit()  # Terminates the execution of a Python program"""

    def update_note_tabs(self, message):
        """ Helper function to update both note_tab2 and note_tab4. """
        self.note_tab2.configure(text=message)
        self.note_tab3.configure(text=message)
        self.note_tab4.configure(text=message)

    def process_modem_response(self, read_val):
        self.process_modem_response_call.process_modem_response_sub(read_val)

    def send_at_command(self):
        """
        Send command from the entry filed - Green
        :return:
        """
        self.at_command = self.enter_command.get("1.0", "end-1c").encode()  # Get AT+ Command
        if self.at_command.decode().startswith('#'):
            print("Commented out: " + str(self.at_command))
        elif self.at_command.decode() == "+++":
            print("Sent command: " + str(self.at_command))
            self.com_port.write(self.at_command)  # Send command + RTN
        else:
            print("Sent command: " + str(self.at_command))
            self.com_port.write(self.at_command + rtn.encode())

    def send_at_command_tab5(self):
        self.at_command_tab5 = self.enter_command_tab5.get("1.0", "end-1c").encode()  # Get AT+ Command
        if self.at_command_tab5.decode().startswith('#'):
            print("Commented out: " + str(self.at_command_tab5))
        else:
            print("Sent command: " + str(self.at_command_tab5))
            self.com_port.write(self.at_command_tab5 + rtn.encode())

    def open_file(self):
        new_window = Toplevel(self.top_level)
        FileEditorApp(new_window)

    def send_at_command_drop_down(self):
        """
        Send command from the dropdown menu
        :return:
        """
        self.at_command = self.selected_option_list_a.get()
        print("Sent command: {} over COM PORT {}".format(self.at_command, self.com_port))
        self.com_port.write(self.at_command.encode() + rtn.encode())

    def send_at_command_drop_down_list_c(self):
        """
        Send command from the dropdown menu
        :return:
        """
        self.at_command = self.selected_option_list_c.get()
        print("Sent command: {} over COM PORT {}".format(self.at_command, self.com_port))
        self.com_port.write(self.at_command.encode() + rtn.encode())

    def send_at_command_drop_down_cat1(self):
        """
        Send command from the dropdown menu
        :return:
        """
        self.at_command = self.selected_option_cat1.get()
        print("Sent command: {} over COM PORT {}".format(self.at_command, self.com_port))
        self.com_port.write(self.at_command.encode() + rtn.encode())

    def display_comport_settings(self, settings_text):
        try:
            # self.com_port_settings.config(text=settings_text)
            # self.com_port_settings_tab1.config(text=settings_text)
            self.ser_port_settings_tab1.delete('1.0', tk.END)
            self.ser_port_settings_tab1.insert('1.0', settings_text)
        except serial.SerialException as e:
            print(f"Error getting comport settings: {e}")

    def read_response(self):
        read_val = self.com_port.read(256)
        if read_val:
            print("Response: " + read_val.decode())  # Convert bytes to a string and print

    def exit_app(self):
        print('exit method called')
        self.stop = True
        return

    def save_lte_resp_to_file(self):
        """
         The "a+" mode when opening the file. This mode opens the file in both append and read mode.
         If the file doesn't exist, it will be created, and if it does exist, new content will be appended to it.
        :return:
        """
        content = self.displ_modem_response_tab2.cget("text")  # Get the text from the LTE Response labelC
        if content:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
            if file_path:
                with open(file_path, "a+") as file:
                    file.write(content + "\n")
                print("Content saved to:", file_path)

    def start_reading_thread(self):
        print("Reading COM PORT {}".format(self.com_port))
        threading.Thread(target=self.read_modem_response_continuously).start()

    def select_and_assign_com_port_from_drop_down_tab1(self):
        self.baud, self.com_port = self.serial_comm.select_and_assign_com_port_from_drop_down()
        return

    def get_com_ports(self):
        """
        This function retrieves information about available communication ports on the system.
        Basically, it initializes comm ports on start.
        List of comports for the COM port drop down. Runs on __init__:
        :return:
        """
        self.com_ports = [port for port in serial.tools.list_ports.comports()]

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

    def get_serial_continuously(self):
        while True:
            self.get_com_ports()
            # self.init_com_port_on_start()

    def get_serial_port_thread(self):
        threading.Thread(target=self.get_serial_continuously).start()


def start_reading_thread_1(com_port, lte_class):
    print("Reading COM PORT {}".format(com_port))
    threading.Thread(target=lte_class.read_modem_response_continuously).start()


if __name__ == '__main__':
    print(os.getcwd())
    try:
        logging.basicConfig(
            filename='logs/log.log',
            filemode='w',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    except Exception as e:
        print("Error configuring logging: {}".format(e))
    input_file = "support_files/command_sequence_files/BG95.txt"
    root = tk.Tk()
    root.title("LTE Modem Communication Serial Interface")
    root.geometry("1210x650")
    root.configure(bg="black")
    window_width = root.winfo_screenwidth()  # Get the width of the window
    lte_commands = LteInterface(root, input_file)
    opened_port = lte_commands.com_port
    time.sleep(0.1)
    # lte_commands.start_reading_thread()
    start_reading_thread_1(opened_port, lte_commands)
    root.mainloop()
