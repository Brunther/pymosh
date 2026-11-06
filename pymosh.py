import inspect
import json
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import filedialog

from PIL import Image, ImageTk, UnidentifiedImageError

from registry import REGISTRY, run_effect


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
        self.bg0 = "#181818"
        self.bg1 = "#333333"
        self.bg2 = "#222222"
        
        ##undo budget
        self.undo_budget = 500
        self.max_undos = 50
        
        ##zooming and panning
        self.zooming = False
        self.zoom_after_id = None
        self.zoom = 1.0
        self.min_zoom = 0.2
        self.max_zoom = 5.0
        self.zoom_step = 0.1
        self.pan_x = 0
        self.pan_y = 0
        self.pan_start = None
        self.zoom_to_mouse = True
        
        
        ##misc
        self.last_status_text = None
        self.settings_open = False
        self.effects_open = False
        
        
        ##settings and path stuff
        pymosh_dir = Path.home() / 'AppData/Roaming/PYMOSH'
        
        self.settings_file = pymosh_dir / 'settings.json'
        
        icon_path = Path(__file__).resolve().parent / 'misc' / 'pymosh.ico'
        self.root.iconbitmap(str(icon_path))
        
        self.default_settings = {
                    "preview_sampling": "NEAREST NEIGHBOR",
                    "min_zoom": 0.2,
                    "max_zoom": 5.0,
                    "zoom_step": 0.1,
                    "theme_accent": "Neon Green",
                    "max_undos": 50,
                    "undo_budget": 500,
                    "zoom_to_mouse": True
                }
        
        self.load_settings_file()
        
        self.preview_methods = {
            "NEAREST NEIGHBOR": Image.Resampling.NEAREST,
            "BILINEAR": Image.Resampling.BILINEAR,
            "LANCZOS": Image.Resampling.LANCZOS
        }
        
        self.themes = {
            "Neon Green": ("#aaff00", "#ccff66"),
            "Neon Purple": ("#ee11ee", "#ff00ff"),
            "Forest Green": ("#4f7942", "#228b22"),
            "Ocean Blue": ("#009dc4", "#00a7d1"),
        }
        
        ##theme accent
        self.accent1, self.accent2 = self.themes[self.theme_accent]
        
        self.build_gui()
        
        
    def build_gui(self):
        self.toolbar = tk.Frame(root, bg=self.bg2)
        self.toolbar.pack(fill="x")
        
        
        open_button = tk.Button(
            self.toolbar,
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
            self.toolbar,
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
            self.toolbar,
            text="PYMOSH",
            font=("Courier", 24, "bold"),
            fg=self.accent1,
            bg=self.bg2
            )
        header.place(relx=0.5, rely=0.5, anchor="center")
        
        #TODO: search autocomplete / show what each parameter does
        self.search = tk.Entry(
            self.toolbar,
            font=("Courier", 12, "bold"),
            fg=self.accent1,
            bg=self.bg1,
            relief="ridge",
            insertbackground=self.accent1
            
        )
        self.search.pack(side="right", padx=10, pady=10)
        self.search.bind(
            "<Return>",
            self.execute_effect
        )
        
        undo_button = tk.Button(
            self.toolbar,
            text="Undo",
            command=self.undo,
            bg=self.bg1,
            fg="white",
            relief="flat",
            padx=16,
            pady=8
        )
        undo_button.pack(side="right", padx=10, pady=10)
        
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
        
        self.canvas = tk.Canvas(
            self.preview_frame, 
            bg=self.bg0,
            highlightthickness=0,
            bd=0
            )
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas_image = self.canvas.create_image(0, 0, anchor="nw")
        
        ##bindings
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.drag_pan)
        self.canvas.bind("<ButtonRelease-2>", self.end_pan)   
        
        self.canvas.bind("<Control-MouseWheel>", 
                        lambda event: self.change_zoom(
                            self.zoom_step if event.delta > 0 else - self.zoom_step,
                            event.x,
                            event.y
                            )
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
            fg=self.accent1,
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
        self.canvas.bind("<Control-MouseWheel>", 
                           lambda event: self.change_zoom(
                               self.zoom_step if event.delta > 0 else - self.zoom_step,
                               event.x,
                               event.y
                           )
                           )
    
        
    def rebuild_gui(self):
        for widget in self.root.winfo_children():
            widget.destroy()   
        
        self.build_gui()
        self.update_preview()
        
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
        else:
            path = Path(path)
        
        try:
            with Image.open(path) as img:
                self.original_image = img.convert("RGB")
            
            #Make copy for display
            self.image = self.original_image.copy()
            
            self.undo_stack.clear()
            
            self.pan_x = 0
            self.pan_y = 0
            
            self.update_preview()
            
            self.status.configure(
                text=(f"PYMOSH // {path.name.upper()} // {self.image.width}x{self.image.height} PX")
            )
        except UnidentifiedImageError:
            self.status.configure(text="PYMOSH // Error: Cannot identify image file")
        except Exception as error:  # noqa: BLE001
            self.status.configure(text=f"PYMOSH // Error: {error}")
    
    
    
    
    def on_canvas_resize(self, event):
        if self.image is None:
            return
        
        self.update_preview()
    
            
    def update_preview(self):
        if self.image is None:
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        img_width, img_height = self.image.size
        
        base_scale = min(820 / img_width, 520 / img_height)
        scale = base_scale * self.zoom
        
        
        left = (img_width - canvas_width / scale) / 2 - self.pan_x / scale
        top = (img_height - canvas_height / scale) / 2 - self.pan_y / scale
        
        right = left + canvas_width / scale
        bottom = top + canvas_height / scale
        
        crop_left = max(0, int(left))
        crop_top = max(0, int(top))
        crop_right = min(img_width, int(right) + 1)
        crop_bottom = min(img_height, int(bottom) + 1)
        
        if crop_right <= crop_left or crop_bottom <= crop_top:
            return
        
        cropped = self.image.crop((
            crop_left,
            crop_top,
            crop_right,
            crop_bottom
        ))
                
        if self.zooming:
            method=Image.Resampling.BILINEAR
        else:
            method=self.preview_methods[self.preview_sampling]
            
        preview = cropped.resize(
            (
                max(1, round((crop_right - crop_left) * scale)), 
                max(1, round((crop_bottom - crop_top) * scale))
            ),
            resample=method
        )    
        
        self.display_image = ImageTk.PhotoImage(preview)
        
        self.canvas.itemconfigure(
            self.canvas_image,
            image=self.display_image
        )
        
        self.canvas.coords(
            self.canvas_image,
            (crop_left - left) * scale,
            (crop_top - top) * scale
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
                except Exception as error: # noqa: BLE001
                    traceback.print_exc()
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
            (total > self.undo_budget << 20) or len(self.undo_stack) > self.max_undos
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
    
    ##ZOOMING AND PANNING
    def change_zoom(self, amount, mouse_x=None, mouse_y=None):
        
        if self.min_zoom > self.zoom + amount or self.max_zoom < self.zoom + amount:
            return
        
        if not self.zoom_to_mouse:
            mouse_x = None
            mouse_y = None
        
        new_zoom = self.zoom + amount
        old_zoom = self.zoom
        
        center_x = self.canvas.winfo_width() / 2
        center_y = self.canvas.winfo_height() / 2
        
        
        if mouse_x is None:
            mouse_x = center_x
        if mouse_y is None:
            mouse_y = center_y
        
        ratio = new_zoom / old_zoom
        
        self.pan_x = (
            mouse_x - center_x
            - ratio * (mouse_x - center_x - self.pan_x)
        )
        
        self.pan_y = (
            mouse_y - center_y
            - ratio * (mouse_y - center_y - self.pan_y)
        )
        
        self.zoom = new_zoom
        self.zooming = True
        
        if self.zoom_after_id is not None:
            self.root.after_cancel(self.zoom_after_id)
        
        self.update_preview()
        
        self.zoom_after_id = self.root.after(120, self.finish_zoom)
    
    def finish_zoom(self):
        self.zoom_after_id = None
        self.zooming = False
        self.update_preview()
        
    def start_pan(self, event):
        self.pan_start = (event.x, event.y)    
        self.canvas.configure(cursor="fleur")
        
    def drag_pan(self, event):
        if self.pan_start is None:
            return
        
        dx = event.x - self.pan_start[0]
        dy = event.y - self.pan_start[1]
        
        self.pan_x += dx
        self.pan_y += dy
        
        self.pan_start = (event.x, event.y)
        
        self.update_preview()
            
    def end_pan(self, event):
        self.pan_start = None
        self.canvas.configure(cursor="")
        
        
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
            fg=self.accent1
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
            bg=self.accent1,
            activebackground=self.accent2,
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
                fg=self.accent1
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
        settings_title = tk.Label(
            self.settings_frame,
            text="SETTINGS",
            font=("Courier", 18, "bold"),
            bg=self.bg0,
            fg=self.accent1
        )
        settings_title.place(relx=0.5, y=15, anchor="n")
        
        save_settings_button = tk.Button(
            self.settings_frame,
            text="SAVE SETTINGS",
            font=("Courier", 14),
            command=self.save_settings,
            bg=self.bg0,
            fg="white",
            relief="flat",
            padx=16,
            pady=8
        )
        save_settings_button.place(relx=0.5, y=55, anchor="n")
        
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
            bg=self.accent1,
            activebackground=self.accent2,
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
        
        ##theme settings
        tk.Label(
            content,
            text="THEME",
            font=("Courier", 14, "bold"),
            bg=self.bg0,
            fg=self.accent1
        ).pack(anchor="w", pady=(15, 5))
        
        tk.Label(
            content,
            text="ACCENT COLOR",
            font=("Courier", 10),
            bg=self.bg0,
            fg="white"
        ).pack(anchor="w")
        
        accent_var = tk.StringVar(
            value=next(
                name for name, accents in self.themes.items()
                if accents == self.themes[self.theme_accent]
            )
        )
        
        
        ##TODO: FIX THIS SHIT DEADAHH
        def change_accent(selected):
            self.theme_accent = selected
            self.accent1, self.accent2 = self.themes[selected]
            self.settings["theme_accent"] = selected
            
            self.rebuild_gui()
            
            self.settings_open = False
            self.show_settings()
            self.status.configure(text=f"PYMOSH // APPLIED {self.theme_accent.upper()} ACCENT")
            
        accent_menu = tk.OptionMenu(
            content,
            accent_var,
            *self.themes.keys(),
            command=change_accent
        )
        
        accent_menu.configure(
            bg=self.bg2,
            fg=self.accent1,
            activebackground=self.accent2,
            activeforeground="black",
            highlightthickness=1,
            relief="flat",
            font=("Courier", 10)
        )
        accent_menu["menu"].configure(
        bg=self.bg2,
        fg=self.accent1,
        activebackground=self.accent2,
        activeforeground="black",
        font=("courier", 10),
        bd=0
        )
        accent_menu.pack(anchor="w", pady=5)
        
        ##preview settings
        tk.Label(
            content,
            text="PREVIEW",
            font=("Courier", 14, "bold"),
            bg=self.bg0,
            fg=self.accent1
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
        
        sampling_menu = tk.OptionMenu(
            content,
            sampling_var,
            *self.preview_methods.keys(),
            command=change_sampling
        )
        sampling_menu.configure(
            bg=self.bg2,
            fg=self.accent1,
            activebackground=self.accent2,
            activeforeground="black",
            highlightthickness=1,
            relief="flat",
            font=("Courier", 10)
        )
        sampling_menu["menu"].configure(
            bg=self.bg2,
            fg=self.accent1,
            activebackground=self.accent2,
            activeforeground="black",
            font=("courier", 10),
            bd=0
        )
        sampling_menu.pack(anchor="w", pady=5)
        
        
        ##zoom settings
        def change_min_zoom(value):
            self.min_zoom = float(value)
            self.settings["min_zoom"] = float(value)
            
            self.zoom = max(self.zoom, self.min_zoom)
            
            self.update_preview()
                    
        def change_max_zoom(value):
            self.max_zoom = float(value)
            self.settings["max_zoom"] = float(value)
            
            self.zoom = min(self.zoom, self.max_zoom)
            
            self.update_preview()
        
        def change_zoom_step(value):
            self.zoom_step = float(value)
            self.settings["zoom_step"] = float(value)     
        
         
                    
                    
        tk.Label(
        content,
        text="ZOOM",
        font=("Courier", 14, "bold"),
        bg=self.bg0,
        fg=self.accent1
        ).pack(anchor="w", pady=(15, 5))

        ##zoom to mouse
        self.zoom_to_mouse_var = tk.BooleanVar(
            value=self.zoom_to_mouse
        )
        
        def change_zoom_to_mouse():
            self.zoom_to_mouse = self.zoom_to_mouse_var.get()
            self.settings["zoom_to_mouse"] = self.zoom_to_mouse
            if not self.zoom_to_mouse:
                self.pan_x = 0
                self.pan_y = 0
                self.update_preview()
        
        
        zoom_row = tk.Frame(content, bg=self.bg0)
        zoom_row.pack(anchor="w")
        
        tk.Label(
            zoom_row,
            text="ZOOM TO MOUSE",
            font=("Courier", 10),
            bg=self.bg0,
            fg="white"
        ).pack(side="left")
        
        
        tk.Checkbutton(
            zoom_row,
            variable=self.zoom_to_mouse_var,
            command=change_zoom_to_mouse,
            font=("Courier", 6),
            bg=self.bg0,
            fg=self.accent1,
            selectcolor=self.bg0,
            activeforeground=self.accent1,
            bd=0,
            padx=0,
            pady=0,
            width=0,
            anchor="center",
        ).pack(side="left", padx=(8, 0), pady=0)


        #min zoom
        tk.Label(
        content,
        text="MIN ZOOM",
        font=("Courier", 10),
        bg=self.bg0,
        fg="white"
        ).pack(anchor="w")
        
        min_zoom_slider = tk.Scale(
        content,
        from_=0.1,
        to=1,
        orient="horizontal",
        resolution=0.05,
        command=change_min_zoom
        )
        min_zoom_slider.configure(
            bg=self.bg2,
            fg=self.accent1,
            troughcolor="#222222",
            activebackground=self.accent2,
            highlightthickness=1,
            highlightbackground="white",
            highlightcolor=self.accent1,
            relief="flat",
            font=("Courier", 10, "bold"),
            width=10,
            sliderlength=16,
            length=180
        )
        min_zoom_slider.set(self.settings.get("min_zoom", self.min_zoom))
        min_zoom_slider.pack(anchor="w", pady=5)
        
        #max zoom
        tk.Label(
        content,
        text="MAX ZOOM",
        font=("Courier", 10),
        bg=self.bg0,
        fg="white"
        ).pack(anchor="w")
        
        max_zoom_slider = tk.Scale(
        content,
        from_=1,
        to=10,
        orient="horizontal",
        resolution=0.1,
        command=change_max_zoom
        )
        max_zoom_slider.configure(
            bg=self.bg2,
            fg=self.accent1,
            troughcolor="#222222",
            activebackground=self.accent2,
            highlightthickness=1,
            highlightbackground="white",
            highlightcolor=self.accent1,
            relief="flat",
            font=("Courier", 10, "bold"),
            width=10,
            sliderlength=16,
            length=180
        )
        max_zoom_slider.set(self.settings.get("max_zoom", self.max_zoom))
        max_zoom_slider.pack(anchor="w", pady=5)
        
        #zoom step
        tk.Label(
        content,
        text="ZOOM STEP",
        font=("Courier", 10),
        bg=self.bg0,
        fg="white"
        ).pack(anchor="w")
        
        zoom_step_slider = tk.Scale(
        content,
        from_=0.05,
        to=1,
        orient="horizontal",
        resolution=0.05,
        command=change_zoom_step
        )
        zoom_step_slider.configure(
            bg=self.bg2,
            fg=self.accent1,
            troughcolor="#222222",
            activebackground=self.accent2,
            highlightthickness=1,
            highlightbackground="white",
            highlightcolor=self.accent1,
            relief="flat",
            font=("Courier", 10, "bold"),
            width=10,
            sliderlength=16,
            length=180
        )
        zoom_step_slider.set(self.settings.get("zoom_step", self.zoom_step))
        zoom_step_slider.pack(anchor="w", pady=5)
        
        def change_undo_count(value):
            self.max_undos = int(value)
            self.settings["max_undos"] = int(value)
            
        def change_undo_budget(value):
            self.undo_budget = int(value)
            self.settings["undo_budget"] = int(value)
        
        ##undo budget
        tk.Label(
        content,
        text="UNDOS",
        font=("Courier", 14, "bold"),
        bg=self.bg0,
        fg=self.accent1
        ).pack(anchor="w", pady=(15, 5))

        #min zoom
        tk.Label(
        content,
        text="MAX UNDO COUNT",
        font=("Courier", 10),
        bg=self.bg0,
        fg="white"
        ).pack(anchor="w")
        
        undo_count_slider = tk.Scale(
        content,
        from_=20,
        to=200,
        orient="horizontal",
        resolution=1,
        command=change_undo_count
        )
        undo_count_slider.configure(
            bg=self.bg2,
            fg=self.accent1,
            troughcolor="#222222",
            activebackground=self.accent2,
            highlightthickness=1,
            highlightbackground="white",
            highlightcolor=self.accent1,
            relief="flat",
            font=("Courier", 10, "bold"),
            width=10,
            sliderlength=16,
            length=180
        )
        undo_count_slider.set(self.settings.get("max_undos", self.max_undos))
        undo_count_slider.pack(anchor="w", pady=5)
        
        #max zoom
        tk.Label(
        content,
        text="UNDO BUDGET (Mb RAM)",
        font=("Courier", 10),
        bg=self.bg0,
        fg="white"
        ).pack(anchor="w")
        
        undo_budget_slider = tk.Scale(
        content,
        from_=10,
        to=2500,
        orient="horizontal",
        resolution=10,
        command=change_undo_budget
        )
        undo_budget_slider.configure(
            bg=self.bg2,
            fg=self.accent1,
            troughcolor="#222222",
            activebackground=self.accent2,
            highlightthickness=1,
            highlightbackground="white",
            highlightcolor=self.accent1,
            relief="flat",
            font=("Courier", 10, "bold"),
            width=10,
            sliderlength=16,
            length=180
        )
        undo_budget_slider.set(self.settings.get("undo_budget", self.undo_budget))
        undo_budget_slider.pack(anchor="w", pady=5)
        
        ##for scrolling
        bind_mousewheel(content)
        settings_title.lift()
        save_settings_button.lift()
        
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
        self.settings = self.default_settings.copy()
        
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r") as file:
                    settings = json.load(file)
                    self.settings.update(settings)
            except (json.JSONDecodeError, OSError):
                pass
        
        self.save_settings()
            
        self.theme_accent = self.settings["theme_accent"]
        self.preview_sampling = self.settings["preview_sampling"]
        self.min_zoom = self.settings["min_zoom"]
        self.max_zoom = self.settings["max_zoom"]
        self.zoom_step = self.settings["zoom_step"]
        self.max_undos = self.settings["max_undos"]
        self.undo_budget = self.settings["undo_budget"]
        self.zoom_to_mouse = self.settings["zoom_to_mouse"]
    
    def save_settings(self):
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.settings_file, "w") as file:
            json.dump(self.settings, file, indent=4)
        
        if hasattr(self, "status"):
            self.status.configure(text="PYMOSH // SETTINGS SAVED")
        
        
root = tk.Tk()
app = PyMosh(root)
root.mainloop()