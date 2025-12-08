#!/usr/bin/env python3
"""
UI Components - Handles all UI setup and layout for Nebulatro
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path


class UIComponents:
    """Manages UI layout and components"""
    
    def __init__(self, root, bg_color='#2b2b2b', canvas_bg='#1e1e1e'):
        self.root = root
        self.bg_color = bg_color
        self.canvas_bg = canvas_bg
        
        # UI elements (will be set by setup methods)
        self.modifiers_canvas = None
        self.card_grid_canvas = None
        self.order_canvas = None
        self.order_frame = None
        
        # Filter variables
        self.modifier_filter = tk.StringVar(value="All Modifiers")
        self.card_contrast = tk.StringVar(value="Standard")
        self.face_card_collabs = {
            'spades': tk.StringVar(value="Default"),
            'hearts': tk.StringVar(value="Default"),
            'clubs': tk.StringVar(value="Default"),
            'diamonds': tk.StringVar(value="Default")
        }
    
    def set_app_icon(self):
        """Set application icon"""
        try:
            for icon_file in ["app_icon.icns", "app_icon.png"]:
                icon_path = Path(icon_file)
                if icon_path.exists():
                    icon_img = Image.open(icon_path)
                    if icon_img.size[0] > 256 or icon_img.size[1] > 256:
                        icon_img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                    icon_photo = ImageTk.PhotoImage(icon_img)
                    self.root.iconphoto(True, icon_photo)
                    self.root._icon_photo = icon_photo
                    break
        except Exception as e:
            print(f"Warning: Could not set app icon: {e}")
    
    def setup_main_layout(self, card_display_width, card_display_height, 
                         on_modifier_filter_change, on_card_design_click,
                         on_clear, on_undo, on_save):
        """Create the main UI layout"""
        # Configure root
        self.root.configure(bg=self.bg_color)
        
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=10, pady=10)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title and filter row
        self._setup_title_and_filters(main_frame, on_modifier_filter_change, on_card_design_click)
        
        # Modifiers canvas
        self.modifiers_canvas = tk.Canvas(main_frame, bg=self.bg_color, highlightthickness=0)
        self.modifiers_canvas.grid(row=1, column=0, pady=(0, 5))
        
        # Card grid canvas
        self.card_grid_canvas = tk.Canvas(main_frame, bg=self.bg_color, highlightthickness=0)
        self.card_grid_canvas.grid(row=2, column=0, pady=10)
        
        # Separator
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Order list
        self._setup_order_list(main_frame)
        
        # Buttons
        self._setup_buttons(main_frame, on_clear, on_undo, on_save)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
    
    def _setup_title_and_filters(self, parent, on_modifier_filter_change, on_card_design_click):
        """Setup title and filter controls"""
        title_frame = tk.Frame(parent, bg=self.bg_color)
        title_frame.grid(row=0, column=0, pady=10)
        
        title = tk.Label(title_frame, text="Click a card to add to sequence", 
                        font=('Arial', 14, 'bold'),
                        bg=self.bg_color, fg='white')
        title.pack(side=tk.LEFT, padx=(0, 20))
        
        filter_label = tk.Label(title_frame, text="Filters:", 
                               font=('Arial', 11),
                               bg=self.bg_color, fg='white')
        filter_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Modifier filter dropdown
        modifier_options = ["All Modifiers", "Scoring Only"]
        modifier_menu = ttk.Combobox(title_frame, textvariable=self.modifier_filter,
                                    values=modifier_options, state='readonly', width=15)
        modifier_menu.pack(side=tk.LEFT, padx=5)
        modifier_menu.bind('<<ComboboxSelected>>', on_modifier_filter_change)
        
        # Card designs button
        card_design_btn = ttk.Button(title_frame, text="Card Designs...", 
                                     command=on_card_design_click)
        card_design_btn.pack(side=tk.LEFT, padx=5)
    
    def _setup_order_list(self, parent):
        """Setup card order display area"""
        order_label = tk.Label(parent, text="Card Order:", 
                              font=('Arial', 12, 'bold'),
                              bg=self.bg_color, fg='white')
        order_label.grid(row=4, column=0, sticky=tk.W)
        
        order_container = tk.Frame(parent, bg=self.bg_color)
        order_container.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.order_canvas = tk.Canvas(order_container, height=90, 
                                     bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(order_container, orient='horizontal', 
                                 command=self.order_canvas.xview)
        self.order_frame = tk.Frame(self.order_canvas, bg=self.bg_color)
        
        self.order_canvas.configure(xscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.order_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.order_canvas.create_window((0, 0), window=self.order_frame, anchor='nw')
    
    def _setup_buttons(self, parent, on_clear, on_undo, on_save):
        """Setup action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=6, column=0, pady=10)
        
        ttk.Button(button_frame, text="Clear Order", command=on_clear).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Undo Last", command=on_undo).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save", command=on_save).pack(side=tk.LEFT, padx=5)
