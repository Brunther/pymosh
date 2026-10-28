import os
import tkinter as tk
from tkinter import filedialog

from PIL import Image, ImageOps, ImageTk

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
        self.undo_stack = []
        
        ##colors
        self.neon = "#aaff00"
        self.bg1 = "#333333"
        self.bg2 = "#222222"
        
        ##undo budget
        self.undo_budget = 500 << 20
        self.max_undos = 50
        
        ##zooming
        self.zoom = 1.0
        self.min_zoom = 0.2
        self.max_zoom = 5.0
        self.zoom_step = 0.1
        
        ##top toolbar
        toolbar = tk.Frame(root, bg=self.bg2)
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
        self.preview_frame = tk.Frame(
            root,
            bg="#181818"
        )
        self.preview_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )
        
        self.canvas = tk.Label(
            self.preview_frame, 
            text="Open image to get started",
            bg="#181818",
            fg="#888888"
            )
        self.canvas.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
            )
        
        ##bottom status bar
        self.status_bar = tk.Frame(
            root,
            bg=self.bg2,
            height=42
        )
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)
        
        self.status = tk.Label(
            self.status_bar,
            text="PYMOSH // READY",
            font=("Courier", 11, "bold"),
            bg=self.bg2,
            fg=self.neon,
            anchor="w",
            padx=10,
            )
        self.status.pack(side="left", fill="y")
        
        ##settings button TODO: actually make this work
        settings_button = tk.Button(
            self.status_bar,
            text="Settings",
            bg=self.bg1,
            fg="white",
            relief="flat",
            padx=16,
            pady=8
        )
        settings_button.pack(side="right", padx=10, pady=10)
        
        ##show effects button TODO: actually make this work
        effects_button = tk.Button(
            self.status_bar,
            text="Effects",
            bg=self.bg1,
            fg="white",
            relief="flat",
            padx=16,
            pady=8
        )
        effects_button.pack(side="right", padx=10, pady=10)

        
        ##ZOOMING
        self.root.bind_all("<Control-MouseWheel>", self.zoom_image)
        
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
            
            self.undo_stack.clear()
            
            self.update_preview()
            
            self.status.configure(
                text=(f"PYMOSH // {os.path.basename(path).upper()} // {self.image.width}x{self.image.height} PX")
            )
        except Exception as error:  # noqa: BLE001
            self.status.configure(text=f"Error // {error}")
            
    def update_preview(self):
        if self.image is None:
            return
        max_width = int(820 * self.zoom)
        max_height = int(520 * self.zoom)
        preview = ImageOps.contain(
            self.image,
            (max_width, max_height),
            method=Image.Resampling.LANCZOS
        )
        
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
        
        query = self.search.get().lower().strip()
        parts = query.split(":", 1)
        command = parts[0]
        try:
            
            if command in {"r", "restart", "reset"}:
                self.restart()
            elif command in {"u", "z", "undo"}:
                if len(parts) == 2:
                    try:
                        self.undo(amount=int(parts[1]))
                    except ValueError:
                        raise ValueError("Paramater must be number")
                else:
                    self.undo()
            else:
                result, name = run_effect(parts, self.image)
                
                self.undo_stack.append(self.image)
                self.trim_undo_stack()
                
                self.image = result
                self.update_preview()
                
                self.status.configure(
                    text=f"PYMOSH // APPLIED {name.upper()}"
                )
        except ValueError as error:
            self.status.configure(
                text=f"PYMOSH // {error}"
            )
        return "break"
        
    def trim_undo_stack(self):
        total = sum(
            img.width * img.height * len(img.getbands())
            for img in self.undo_stack
        )
        
        while self.undo_stack and (
            total > self.undo_budget or len(self.undo_stack) > self.max_undos
        ):
            oldest = self.undo_stack.pop(0)
            total -= (oldest.width * oldest.height * len(oldest.getbands()))
    
    def undo(self, amount=1):
        if not self.undo_stack:
            self.status.configure(
                text="PYMOSH // NOTHING TO UNDO"
                )
            return
        if amount > len(self.undo_stack):
            self.restart(status=False)
        else:
            for i in range(amount): 
                self.image = self.undo_stack.pop()
            self.update_preview()
        if amount == 1:
            status = "PYMOSH // APPLIED UNDO"
        else:
            status = f"PYMOSH // APPLIED UNDO x{amount}"
        self.status.configure(
                    text=status
                )   
    def restart(self, status=True):
        self.image = self.original_image.copy()
        self.undo_stack.clear()
        self.update_preview()
        if status:
            self.status.configure(
                text="PYMOSH // APPLIED RESTART"
            )
    
    ##ZOOMING
    def zoom_image(self, event):
        if event.delta > 0:
            self.change_zoom(self.zoom_step)
        else:
            self.change_zoom(self.zoom_step * -1)
        return "break"
    def change_zoom(self, amount):
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom + amount))
        self.update_preview()
        
        
            

root = tk.Tk()
app = PyMosh(root)
root.mainloop()