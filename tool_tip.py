import tkinter as tk
from tkinter import ttk


class Tooltip:
    def __init__(self, widget, text=""):
        self.widget = widget
        self.text = text
        self.tooltip_window = None

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify="left",
                         background="yellow", relief="solid", borderwidth=1,
                         font=("Arial", 10))
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def create_dropdown_with_tooltips(root):
    descriptions = {
        "AT+CSQ": "Signal Quality Report",
        "AT+COPS=?": "List Available Operators",
        "AT+COPS=0": "Automatically Select Operator",
        "AT+CREG?": "Network Registration Status",
        "AT+CPIN?": "SIM PIN Status",
        # Add descriptions for other commands...
    }

    def on_combobox_change(event):
        selected = selected_option_cat1.get()
        tooltip.text = descriptions.get(selected, "No description available")

    selected_option_cat1 = tk.StringVar()
    selected_option_cat1.set("AT+CSQ")
    dropdown_cat1 = ttk.Combobox(root, textvariable=selected_option_cat1,
                                 values=list(descriptions.keys()),
                                 width=21, height=5)
    dropdown_cat1.grid(column=0, row=0, padx=10, pady=10)
    dropdown_cat1.bind("<<ComboboxSelected>>", on_combobox_change)

    tooltip = Tooltip(dropdown_cat1, text=descriptions["AT+CSQ"])
    dropdown_cat1.bind("<Enter>", tooltip.show_tooltip)
    dropdown_cat1.bind("<Leave>", tooltip.hide_tooltip)


"""root = tk.Tk()
create_dropdown_with_tooltips(root)
root.mainloop()"""
