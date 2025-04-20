from tkinter.ttk import Frame
from PIL import Image, ImageTk
import tkinter as tk
import webbrowser


class DisplayImagesUserInterfaceInit(Frame):
    def __init__(self):
        super().__init__()

        # Images ---------------------------------------------------------------
        self.exit_img = Image.open("img/exit.jpg")
        self.exit_img = self.exit_img.resize((150, 25), Image.LANCZOS)
        self.exit_img = ImageTk.PhotoImage(self.exit_img)

        # Symphony image with clickable link
        self.image_tab1 = Image.open("img/symphony1.jpeg")
        self.image_tab1 = self.image_tab1.resize((300, 300), Image.LANCZOS)
        self.image_tab1 = ImageTk.PhotoImage(self.image_tab1)

        # Symphony image with clickable link
        self.image_hover = Image.open("img/symphony1.jpeg")
        self.image_hover = self.image_hover.resize((310, 310), Image.LANCZOS)
        self.image_hover = ImageTk.PhotoImage(self.image_hover)

        # Symphony image with clickable link
        self.image_normal = Image.open("img/symphony1.jpeg")
        self.image_normal = self.image_normal.resize((300, 300), Image.LANCZOS)
        self.image_normal = ImageTk.PhotoImage(self.image_normal)

        # Create a label for the clickable image
        self.image_label = tk.Label(self, image=self.image_tab1)
        self.image_label.pack()  # You can adjust the layout as needed

        # Define the URL
        website_url = "https://www.jinetinnovations.com/"  # Replace with your desired URL

        # Function to open the website
        def open_website(event):
            webbrowser.open(website_url)

        # Bind left-click to open the website
        self.link = self.image_label.bind("<Button-1>", open_website)


# Example usage:
if __name__ == "__main__":
    root = tk.Tk()
    app = DisplayImagesUserInterfaceInit()
    app.pack()
    root.mainloop()
