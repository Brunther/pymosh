import os
import json
import tkinter as tk
import inspect
from tkinter import filedialog, ttk
from registry import REGISTRY
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
        self.bg0 = "#181818"
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
        
        ##misc
        self.last_status_text = None
        self.settings_open = False
        self.effects_open = False
        
        
        ##settings
        self.settings_file = "misc/settings.json"
        
        self.default_settings = {
                    "preview_sampling": "NEAREST NEIGHBOR",
                }
        
        self.load_settings_file()
        
        self.preview_methods = {
            "NEAREST NEIGHBOR": Image.Resampling.NEAREST,
            "BILINEAR": Image.Resampling.BILINEAR,
            "LANCZOS": Image.Resampling.LANCZOS
        }
        
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
            bg=self.bg0
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
            bg=self.bg0,
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
        
        self.settings_button = tk.Button(
            self.status_bar,
            text="Settings",
            command=self.show_settings,
            bg=self.bg1,
            fg="white",
            relief="flat",
            padx=16,
            pady=8
        )
        self.settings_button.pack(side="right", padx=10, pady=10)
        
        self.effects_button = tk.Button(
            self.status_bar,
            text="Effects",
            command=self.show_effects,
            bg=self.bg1,
            fg="white",
            relief="flat",
            padx=16,
            pady=8
        )
        self.effects_button.pack(side="right", padx=10, pady=10)

        
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
            method=self.preview_methods[self.preview_sampling]
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
        parts = query.split(":")
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
                try:
                    result, name = run_effect(parts, self.image)
                    
                    self.undo_stack.append((self.image, name))
                    self.trim_undo_stack()
                    
                    self.image = result
                    self.update_preview()
                    
                    self.status.configure(
                        text=f"PYMOSH // APPLIED {name.upper()}"
                    )
                except ValueError as error:
                    self.status.configure(
                        text=f"PYMOSH // Error: {error}"
                        )
                except Exception as error:
                    print(type(error).__name__, error)
                    self.status.configure(
                        text=f"PYMOSH // ERROR: {type(error).__name__}"
                        )
        except ValueError as error:
            self.status.configure(
                text=f"PYMOSH // Error: {error}"
                )
        return "break"
        
    def trim_undo_stack(self):
        total = sum(
            img[0].width * img[0].height * len(img[0].getbands())
            for img in self.undo_stack
        )
        
        while self.undo_stack and (
            total > self.undo_budget or len(self.undo_stack) > self.max_undos
        ):
            oldest = self.undo_stack.pop(0)[0]
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
                self.image, name = self.undo_stack.pop()
            self.update_preview()
        if amount == 1:
            status = f"PYMOSH // UNDID {name.upper()}"
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
            self.change_zoom(-self.zoom_step)
        return "break"
    def change_zoom(self, amount):
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom + amount))
        self.update_preview()
        
    ##effects tab
    def show_effects(self):
        if getattr(self, "effects_open", False):
            self.close_effects()
            return
        if self.settings_open:
            self.close_settings()
        self.effects_open = True

        self.last_status_text = self.status.cget("text")
        
        self.preview_frame.pack_forget()
        
        self.effects_frame = tk.Frame(self.root, bg=self.bg0)
        self.effects_frame.pack(
            fill="both", expand=True, padx=20, pady=20
        )
        
        ##Header
        tk.Label(
            self.effects_frame,
            text="EFFECTS",
            font=("Courier", 18, "bold"),
            bg=self.bg0,
            fg=self.neon
        ).pack(anchor="w", pady=(0, 10))
        
        ##scrollable shi
        canvas = tk.Canvas(
            self.effects_frame,
            bg=self.bg0,
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            self.effects_frame,
            orient="vertical",
            command=canvas.yview,
            width=20,
            troughcolor="#111111",
            bg=self.neon,
            activebackground="#ccff66",
            relief="flat",
            bd=0
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        
        content = tk.Frame(canvas, bg=self.bg0)
        content_id = canvas.create_window(
            (0, 0), window=content, anchor="nw"
        )
        
        content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(content_id, width=e.width)
        )
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            canvas.yview_scroll(
                -1 * (event.delta // 120),
                "units"
            )
        canvas.bind("<MouseWheel>", on_mousewheel)
        content.bind("<MouseWheel>", on_mousewheel)
        
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", on_mousewheel) 
            for child in widget.winfo_children():
                bind_mousewheel(child)
        
        ##entry generator
        for code, effect in REGISTRY.items():
            names = effect["name"]
            func = effect["function"]
            defaults = effect.get("default", ())
            description = effect["description"]

            if not isinstance(defaults, (tuple, list)):
                defaults = (defaults,)
            
            params = list(inspect.signature(func).parameters.values())[1:]
            
            card = tk.Frame(
                content,
                bg=self.bg2,
                padx=12,
                pady=10
            )
            card.pack(fill="x", padx=2, pady=5)

            tk.Label(
                card,
                text=f"[{code}] {names[0].upper()}",
                font=("Courier", 14, "bold"),
                bg=self.bg2,
                fg=self.neon
            ).pack(anchor="w")
            
            tk.Label(
                card,
                text=f"Aliases: {', '.join(names[1::])}",
                font=("Courier", 12, "bold"),
                bg=self.bg2,
                fg="white"
            ).pack(anchor="w", pady=(3, 0))
            
            tk.Label(
                card,
                text=description,
                font=("Courier", 10),
                bg=self.bg2,
                fg="#bbbbbb",
                wraplength=650,
                justify="left"
            ).pack(anchor="w", pady=5)
            
            if defaults:
                tk.Label(
                    card,
                    text="Parameter defaults:",
                    font=("Courier", 10),
                    bg=self.bg2,
                    fg="white",
                ).pack(anchor="w")
            else:
                tk.Label(
                    card,
                    text="No default parameters.",
                    font=("Courier", 10),
                    bg=self.bg2,
                    fg="white",
                ).pack(anchor="w")
            
            for i, param in enumerate(params):
                if i < len(defaults):
                    default = repr(defaults[i])
                elif param.default is not inspect.Parameter.empty:
                    default = repr(param.default)
                else:
                    default = "required"
                
                tk.Label(
                    card,
                    text=f"{param.name}: {default}",
                    font=("Courier", 9),
                    bg=self.bg2,
                    fg="#bbbbbb"
                ).pack(anchor="w")
        
        bind_mousewheel(content)
        
        
        self.effects_button.configure(text="Back to editing")
        self.status.configure(text="PYMOSH // EFFECTS")
    
    def close_effects(self):
        self.effects_frame.destroy()
        self.effects_open = False
        self.root.unbind_all("<MouseWheel>")
        
        self.preview_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )
        
        self.effects_button.configure(text="Effects")
        self.status.configure(text=self.last_status_text)
        
    ##settings tab
    def show_settings(self):
        if getattr(self, "settings_open", False):
            self.close_settings()
            return
        if self.effects_open:
            self.close_effects()
        self.settings_open = True
        
        self.last_status_text = self.status.cget("text")
        
        self.preview_frame.pack_forget()
        
        self.settings_frame = tk.Frame(self.root, bg=self.bg0)
        self.settings_frame.pack(
            fill="both", expand=True, padx=20, pady=20
        )
        
        ##Header
        tk.Label(
            self.settings_frame,
            text="SETTINGS",
            font=("Courier", 18, "bold"),
            bg=self.bg0,
            fg=self.neon
        ).pack(anchor="w", pady=(0, 10))
        
        ##scrollable shi
        canvas = tk.Canvas(
            self.settings_frame,
            bg=self.bg0,
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            self.settings_frame,
            orient="vertical",
            command=canvas.yview,
            width=20,
            troughcolor="#111111",
            bg=self.neon,
            activebackground="#ccff66",
            relief="flat",
            bd=0
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        
        content = tk.Frame(canvas, bg=self.bg0)
        content_id = canvas.create_window(
            (0, 0), window=content, anchor="nw"
        )
        
        content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(content_id, width=e.width)
        )
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            canvas.yview_scroll(
                -1 * (event.delta // 120),
                "units"
            )
        canvas.bind("<MouseWheel>", on_mousewheel)
        content.bind("<MouseWheel>", on_mousewheel)
        
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", on_mousewheel) 
            for child in widget.winfo_children():
                bind_mousewheel(child)
                
                
        ##TODO: add settings and whatnot
        ##preview sampling (nearest, bicubic etc), themes (colors), zooming amounts, 
        ##undo budget / max undos, 
        
        ##preview settings
        tk.Label(
            content,
            text="PREVIEW",
            font=("Courier", 14, "bold"),
            bg=self.bg0,
            fg=self.neon
        ).pack(anchor="w", pady=(15, 5))
        
        tk.Label(
            content,
            text="IMAGE SAMPLING",
            font=("Courier", 10),
            bg=self.bg0,
            fg="white"
        ).pack(anchor="w")
        
        sampling_var = tk.StringVar(
            value=next(
                name for name, method in self.preview_methods.items()
                if method == self.preview_methods[self.preview_sampling]
            )
        )
        def change_sampling(selected):
            self.preview_sampling = selected
            self.settings["preview_sampling"] = selected
            
            self.status.configure(text=f"PYMOSH // APPLIED {self.preview_sampling} SAMPLING")
            self.update_preview()
            self.save_settings()
        
        sampling_menu = tk.OptionMenu(
            content,
            sampling_var,
            *self.preview_methods.keys(),
            command=change_sampling
        )
        sampling_menu.configure(
            bg=self.bg2,
            fg=self.neon,
            activebackground="#ccff66",
            activeforeground="black",
            highlightthickness=1,
            relief="flat",
            font=("Courier", 10)
        )
        sampling_menu["menu"].configure(
            bg=self.bg2,
            fg=self.neon,
            activebackground="#ccff66",
            activeforeground="black",
            font=("courier", 10),
            bd=0
        )
        sampling_menu.pack(anchor="w", pady=5)
        
        self.settings_button.configure(text="Back to editing")
        self.status.configure(text="PYMOSH // SETTINGS")
    
    def close_settings(self):
        self.settings_frame.destroy()
        self.settings_open = False
        self.root.unbind_all("<MouseWheel>")
        
        self.preview_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )
        
        self.settings_button.configure(text="Settings")
        self.status.configure(text=self.last_status_text)
        
    def load_settings_file(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as file:
                    settings = json.load(file)
            except (json.JSONDecodeError, OSError):
                settings = self.default_settings.copy()
        else:
            settings = self.default_settings.copy()
        
        self.settings = self.default_settings.copy()
        self.settings.update(settings)
        
        self.preview_sampling = self.settings["preview_sampling"]
    
    def save_settings(self):
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        print("saved settings")
        with open(self.settings_file, "w") as file:
            json.dump(self.settings, file, indent=4)
        
        
root = tk.Tk()
app = PyMosh(root)
root.mainloop()