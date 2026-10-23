import os
import tkinter as tk
from tkinter import filedialog

from PIL import Image, ImageTk

from registry import run_effect


class PyMosh:
    def __init__(self, root):
        self.root = root
        self.root.title("PYMOSH")
        self.root.geometry("900x650")
        self.root.configure(bg="#141414")
        
        ##image
        self.original_image = None
        self.image = None
        self.display_image = None
        
        ##colors
        self.neon = "#aaff00"
        self.bg1 = "#333333"
        self.bg2 = "#222222"
        
        ##top toolbar
        toolbar = tk.Frame(root, bg="#222222")
        toolbar.pack(fill="x")
        
        open_button = tk.Button(
            toolbar,
            text="Open Image",
            command=self.open_image,
            bg=self.bg1,
            fg="white",
            relief="flat",
            padx=16,
            pady=8
        )
        open_button.pack(side="left", padx=10, pady=10)
        
        save_button = tk.Button(
            toolbar,
            text="Save Image",
            command=self.save_image,
            bg=self.bg1,
            fg="white",
            relief="flat",
            padx=16,
            pady=8
        )
        save_button.pack(side="left", padx=10, pady=10)
        
        header = tk.Label(
            toolbar,
            text="PYMOSH",
            font=("Courier", 24, "bold"),
            fg=self.neon,
            bg=self.bg2
            )
        header.place(relx=0.5, rely=0.5, anchor="center")
        
        #TODO: search autocomplete / show what each parameter does
        self.search = tk.Entry(
            toolbar,
            font=("Courier", 12, "bold"),
            fg=self.neon,
            bg=self.bg1,
            relief="ridge",
            insertbackground=self.neon
            
        )
        self.search.pack(side="right", padx=10, pady=10)
        self.search.bind(
            "<Return>",
            self.execute_effect
        )
        
        ##main image display
        self.canvas = tk.Label(
            root, 
            text="Open image to get started",
            bg="#181818",
            fg="#888888"
            )
        self.canvas.pack(
            fill="both", 
            expand=True,
            padx=20,
            pady=20
            )
        
        ##bottom status bar
        self.status = tk.Label(
            root,
            text="PYMOSH // READY",
            font=("Courier", 11, "bold"),
            bg="#222222",
            fg=self.neon,
            anchor="w",
            padx=10,
            pady=8
            )
        self.status.pack(fill="x", side="bottom")
    
    def open_image(self):
        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff"),
                ("All files", "*.*")
            ]
        )
        ##user cancel
        if not path:
            return
        
        try:
            with Image.open(path) as img:
                self.original_image = img.convert("RGB")
            
            #Make copy for display
            self.image = self.original_image.copy()
            
            self.update_preview()
            
            self.status.configure(
                text=(f"PYMOSH // {os.path.basename(path).upper()} // {self.image.width}x{self.image.height} PX")
            )
        except Exception as error:  # noqa: BLE001
            self.status.configure(text=f"Error // {error}")
            
    def update_preview(self):
        if self.image is None:
            return
        
        preview = self.image.copy()
        preview.thumbnail((820, 520))
        
        self.display_image = ImageTk.PhotoImage(preview)
        
        #put image inside window
        self.canvas.configure(
            image=self.display_image,
            text=""
        )        
    
    def save_image(self):
        if self.image is None:
            return
        
        path = filedialog.asksaveasfilename(
            title="Save Image",
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpeg")
            ]
        )
        
        if not path:
            return
        
        self.image.save(path)
        
        self.status.configure(
            text=f"PYMOSH // SAVED: {path.split('/')[-1]}"
        )
    
    
    def execute_effect(self, event=None):
        if self.original_image is None:
            self.status.configure(
                text="PYMOSH // OPEN AN IMAGE FIRST"
            )
            return "break"
        
        query = self.search.get()
        
        image = self.image.copy() if hasattr(self, 'image') and self.image is not None else self.original_image.copy()
        
        try:
            self.image, name = run_effect(
                query, image.copy()
            )
            
            self.update_preview()
            
            self.status.configure(
                text=f"PYMOSH // APPLIED {name.upper()}"
            )
        except ValueError as error:
            self.status.configure(
                text=f"PYMOSH // {error}"
            )
        return "break"
            

root = tk.Tk()
app = PyMosh(root)
root.mainloop()