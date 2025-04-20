import json
import tkinter as tk
from tkinter import messagebox


def update_json(file_path, key, value):
    if not key or not value:
        messagebox.showwarning("Input Error", "Both fields must be filled out!")
        return

    try:
        with open(file_path, "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    data[key] = value

    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)

    messagebox.showinfo("Success", "Entry added!")


def on_submit():
    key = entry_key.get().strip()
    value = entry_value.get("1.0", tk.END).strip()
    update_json("resources/list_b_commands.json", key, value)
    entry_key.delete(0, tk.END)
    entry_value.delete("1.0", tk.END)


if __name__ == "__main__":
    # GUI Setup
    root = tk.Tk()
    root.title("Update JSON File")

    tk.Label(root, text="AT Command:").grid(row=0, column=0, padx=5, pady=5)
    entry_key = tk.Entry(root, width=40)
    entry_key.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(root, text="Description:").grid(row=1, column=0, padx=5, pady=5)
    entry_value = tk.Text(root, width=40, height=4)
    entry_value.grid(row=1, column=1, padx=5, pady=5)

    tk.Button(root, text="Add to JSON", command=on_submit).grid(row=2, columnspan=2, pady=10)

    root.mainloop()
