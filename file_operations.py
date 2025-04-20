import os
import tkinter as tk
from tkinter import filedialog
import re


class FileEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Editor")
        self.text = tk.Text(self.root)
        self.text.pack(fill=tk.BOTH, expand=True)
        self.open_button = tk.Button(self.root, text="Open File", command=self.open_file)
        self.open_button.pack(side=tk.LEFT, padx=5, pady=10)  # Pack to the left

        self.save_button = tk.Button(self.root, text="Save File", command=self.save_file)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=10)  # Pack to the left
        self.current_file = None

    def open_file(self):
        file_path = filedialog.askopenfilename(title="Select a file",
                                               filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            self.current_file = file_path
            with open(file_path, "r") as file:
                content = file.read()
                self.text.delete("1.0", tk.END)  # Clear the text widget
                self.text.insert(tk.END, content)

    def save_file(self):
        if self.current_file:
            content = self.text.get("1.0", tk.END)
            with open(self.current_file, "w") as file:
                file.write(content)
            print("File saved.")
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path = filedialog.asksaveasfilename(title="Save file as", defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            self.current_file = file_path
            content = self.text.get("1.0", tk.END)
            with open(file_path, "w") as file:
                file.write(content)
            print("File saved.")


def count_bytes_in_file(file_path):
    """
    # Example usage:
    file_path = "example.txt"
    byte_count = count_bytes_in_file(file_path)
    if byte_count is not None:
        print(f"The file {file_path} contains {byte_count} bytes.")
    Opens a file, reads its contents, and returns the number of bytes.
    Args:
        file_path (str): The path to the file.
    Returns:
        int: The number of bytes in the file.
    """
    try:
        with open(file_path, 'rb') as file:
            file_contents = file.read()
            byte_count = len(file_contents)
            return byte_count
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def check_file_size(file_path, max_size_mb):
    """Checks the size of a file and deletes it if it exceeds the maximum size."""

    file_size_bytes = os.path.getsize(file_path)
    max_size_bytes = max_size_mb * 1024 * 1024

    if file_size_bytes > max_size_bytes:
        os.remove(file_path)
        print(f"Deleted {file_path} because it exceeded {max_size_mb} MB.")


def test_if_file_exists(filename_to_check):
    if os.path.isfile(filename_to_check):
        print("The file exists " + str(filename_to_check))
        return True
    else:  # If the file does not exist
        print("File does not exist " + str(filename_to_check))
        try:
            file = open(filename_to_check, "w")  # Create the file
        except IOError:
            print("Cannot create file" + str(filename_to_check))
            return False
        file.write("\nNONE NONE\nNONE NONE\nNONE NONE\nNONE NONE\nNONE NONE\n")  # Write to file with the default values
        file.close()
        return False


def process_files(data_file, cat1_file, output_file):
    # Read log.csv content
    with open(data_file, 'r', encoding='utf-8') as f:
        log_content = f.read().strip()

    # Read CAT1 file content
    with open(cat1_file, 'r', encoding='utf-8') as f:
        cat1_content = f.read().strip()

    # Append the log data to the CAT1 content with the required format
    final_content = f"{cat1_content}\n\nrsvp={log_content}"

    # Compute Content-Length
    content_length = len(log_content.encode('utf-8')) + 5

    # Replace existing Content-Length or append if not present
    if "Content-Length:" in final_content:
        final_content = re.sub(r'Content-Length:\s*\d+', f'Content-Length: {content_length}', final_content)
    else:
        final_content = f"{final_content}\nContent-Length: {content_length}"

    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_content)

    print(f"Output saved to {output_file}")


""""# Example usage
process_files('log.csv', 'CAT1', 'output.txt')"""


if __name__ == "__main__":
    root = tk.Tk()
    app = FileEditorApp(root)
    root.mainloop()
