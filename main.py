import os
import glob
import base64
import io
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

from PIL import Image, ImageTk

class ImageTextEditor:
    TEXT_EDITOR_MIN_HEIGHT = 150

    def __init__(self, root):

        self.root = root
        self.root.title("Image Caption Editor")
        self.create_widgets()
        
        self.initialized = False

        # Display the background image
        self.display_image("assets/bg.png")

    def create_widgets(self):
        # Explorer frame
        explorer_frame = ttk.Frame(self.root, padding="5")
        explorer_frame.grid(row=0, column=0, sticky=tk.N+tk.S)

        # Folder explorer
        self.folder_tree = ttk.Treeview(explorer_frame)
        self.folder_tree.pack(side=tk.TOP, fill=tk.Y, expand=True)

        # Viewer and text editor frame
        viewer_text_frame = ttk.Frame(self.root, padding="5")
        viewer_text_frame.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E+tk.W)

        # Image viewer
        image_frame = ttk.Frame(viewer_text_frame)
        image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5))

        self.image_label = ttk.Label(image_frame)
        self.image_label.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(0, 5), pady=(0, 5))

        # Text editor
        text_editor_frame = ttk.Frame(viewer_text_frame)
        text_editor_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.text_editor = tk.Text(text_editor_frame, wrap=tk.WORD)
        self.text_editor.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(0, 5), pady=(0, 5))

        # Buttons
        open_folder_button = ttk.Button(self.root, text="Open Folder", command=self.open_folder)
        open_folder_button.grid(row=1, column=0, sticky=tk.E+tk.W)

        save_button = ttk.Button(self.root, text="Save", command=self.save_text)
        save_button.grid(row=1, column=1, sticky=tk.W)

        batch_replace_button = ttk.Button(self.root, text="Batch Replace", command=self.batch_replace)
        batch_replace_button.grid(row=1, column=1, sticky=tk.E)

        # Configure the column and row weights
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)


    def open_folder(self):
        folder_path = filedialog.askdirectory()

        if folder_path:
            self.current_folder = folder_path
            self.folder_tree.delete(*self.folder_tree.get_children())

            for file in os.listdir(folder_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    self.folder_tree.insert("", tk.END, text=file)

            self.folder_tree.bind("<<TreeviewSelect>>", self.on_file_selected)


    def on_file_selected(self, event):
        selected_items = self.folder_tree.selection()
        
        if not selected_items:
            return

        selected_item = selected_items[0]
        selected_file = self.folder_tree.item(selected_item, "text")

        if selected_file:
            self.current_image_file = os.path.join(self.current_folder, selected_file)
            self.display_image(self.current_image_file)
            self.load_text(self.current_image_file)


    def display_image(self, image_file_path):
        # Load the image
        image = Image.open(image_file_path)

        # Update the application window
        self.root.update_idletasks()

        # Calculate the maximum available size for the image
        max_image_width = max(1, self.root.winfo_width() - self.folder_tree.winfo_width())
        max_image_height = max(1, self.root.winfo_height() - self.TEXT_EDITOR_MIN_HEIGHT)

        # Calculate the new size, preserving the aspect ratio and clamping the maximum size
        new_size = self.calculate_new_size(image, max_image_width, max_image_height)

        # Resize and display the image
        resized_image = image.resize(new_size, Image.LANCZOS)
        tk_image = ImageTk.PhotoImage(resized_image)
        self.image_label.config(image=tk_image)
        self.image_label.image = tk_image

    def load_text(self, image_file_path):
        self.text_editor.delete(1.0, tk.END)

        text_file_path = os.path.splitext(image_file_path)[0] + ".txt"
        self.current_txt_file = text_file_path  # Set the current_txt_file attribute
        if os.path.isfile(text_file_path):
            try:
                with open(text_file_path, "r", encoding="utf-8") as file:
                    file_contents = file.read()
                    self.text_editor.insert(tk.END, file_contents)
            except UnicodeDecodeError:
                messagebox.showerror("Error", "Unable to read the text file. It may be corrupted or in an unsupported format.")

    def save_text(self):
        if not hasattr(self, 'current_txt_file') or not self.current_txt_file:
            return

        # Get the contents of the text editor
        text_contents = self.text_editor.get(1.0, tk.END)

        # Save the contents to the text file
        with open(self.current_txt_file, 'w', encoding='utf-8') as file:
            file.write(text_contents)

        # Show a confirmation message
        tk.messagebox.showinfo("Save", "Text file saved successfully.")


    def batch_replace(self):
        if not hasattr(self, 'current_folder') or not self.current_folder:
            return

        # Ask the user for the search and replace strings
        search_string = tk.simpledialog.askstring("Batch Replace", "Enter the search string:")
        if search_string is None:
            return

        replace_string = tk.simpledialog.askstring("Batch Replace", "Enter the replace string:")
        if replace_string is None:
            return

        # Get all text files in the selected folder
        txt_files = glob.glob(os.path.join(self.current_folder, '*.txt'))

        # Perform the search and replace operation
        for txt_file in txt_files:
            with open(txt_file, 'r', encoding='utf-8') as file:
                file_contents = file.read()

            updated_contents = file_contents.replace(search_string, replace_string)

            with open(txt_file, 'w', encoding='utf-8') as file:
                file.write(updated_contents)

        # Show a confirmation message
        tk.messagebox.showinfo("Batch Replace", "Batch search and replace operation completed successfully.")

    def calculate_new_size(self, image, max_width, max_height):
        original_width, original_height = image.size
        aspect_ratio = float(original_width) / float(original_height)
        
        new_width = min(original_width, max_width)
        new_height = int(new_width / aspect_ratio)

        if new_height > max_height:
            new_height = max_height
            new_width = int(new_height * aspect_ratio)

        return (new_width, new_height)


def main():
    root = tk.Tk()
    root.geometry("800x600")  # Set the initial size of the window
    app = ImageTextEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
