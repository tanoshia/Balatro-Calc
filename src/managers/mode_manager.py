#!/usr/bin/env python3
"""
Mode Manager - Handles mode switching between Manual Tracking and Data Labeling
"""

import tkinter as tk
from PIL import Image


class ModeManager:
    """Manages application mode switching and state"""
    
    def __init__(self, ui, card_manager, labeling_manager, card_display_manager, card_order_config, sprite_loader):
        self.ui = ui
        self.card_manager = card_manager
        self.labeling_manager = labeling_manager
        self.card_display_manager = card_display_manager
        self.card_order_config = card_order_config
        self.sprite_loader = sprite_loader
        
        # Current mode state
        self.current_mode = "Manual Tracking"
        
    def switch_mode(self, new_mode):
        """Switch between Manual Tracking and Data Labeling modes"""
        if new_mode == self.current_mode:
            return
            
        self.current_mode = new_mode
        
        if new_mode == "Manual Tracking":
            self._switch_to_manual_tracking()
        elif new_mode == "Data Labeling":
            self._switch_to_data_labeling()
        
        # Update UI elements for new mode
        self.ui.update_title_for_mode(new_mode)
        self.ui.update_buttons_for_mode(new_mode)
    
    def _switch_to_manual_tracking(self):
        """Switch to manual tracking mode"""
        # Show order list, hide labeling area and suits
        if hasattr(self.ui, 'labeling_frame'):
            self.ui.labeling_frame.grid_remove()
        self.ui.order_frame.grid()
        # Show order label in manual tracking mode
        self.ui.order_label.grid()
        # Show bottom buttons for manual tracking
        self._show_bottom_buttons()
        # Hide suits canvas and center cards
        if hasattr(self.ui, 'suits_canvas'):
            self.ui.suits_canvas.grid_remove()
        self.ui.card_grid_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E))
        # Make column 0 expandable when suits are hidden
        self.ui.card_area_frame.columnconfigure(0, weight=1)
        self.ui.card_area_frame.columnconfigure(1, weight=0)
        
        # Unbind keyboard shortcuts
        self._unbind_labeling_shortcuts()
    
    def _switch_to_data_labeling(self):
        """Switch to data labeling mode"""
        # Hide order list, show labeling area
        self.ui.order_frame.grid_remove()
        if not hasattr(self.ui, 'labeling_frame'):
            # Create labeling area if it doesn't exist
            parent = self.ui.order_frame.master
            self.ui.labeling_frame = self.ui.setup_labeling_area(parent)
            
            # Setup labeling button handlers - delegate to labeling manager
            self._setup_labeling_handlers()
            
            # Bind keyboard shortcuts for data labeling
            self._bind_labeling_shortcuts()
        
        self.ui.labeling_frame.grid(row=4, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Hide order label in data labeling mode (title moved to left column)
        self.ui.order_label.grid_remove()
        
        # Hide bottom buttons in data labeling mode (functionality moved to labeling area)
        self._hide_bottom_buttons()
        
        # Load and display suits for data labeling
        self._load_suits_for_labeling()
        # Show suits canvas in data labeling mode
        if hasattr(self.ui, 'suits_canvas'):
            self.ui.suits_canvas.grid(row=0, column=0, padx=(0, 10))
        self.ui.card_grid_canvas.grid(row=0, column=1, sticky=(tk.W, tk.E))
        # Reset column weights for side-by-side layout
        self.ui.card_area_frame.columnconfigure(0, weight=0)
        self.ui.card_area_frame.columnconfigure(1, weight=1)
    
    def _setup_labeling_handlers(self):
        """Setup labeling button handlers"""
        self.ui.prev_card_btn.configure(command=self.labeling_manager.on_prev_card)
        self.ui.next_card_btn.configure(command=self.labeling_manager.on_next_card)
        self.ui.skip_card_btn.configure(command=self.labeling_manager.on_skip_card)
        self.ui.not_card_btn.configure(command=self.labeling_manager.on_label_not_card)
        self.ui.save_label_btn.configure(command=self.labeling_manager.save_current_label)
        self.ui.load_cards_btn.configure(command=self.labeling_manager.load_cards_for_labeling)
        
        # Additional label category handlers
        self.ui.card_backs_btn.configure(command=self.labeling_manager.on_label_card_backs)
        self.ui.booster_packs_btn.configure(command=self.labeling_manager.on_label_booster_packs)
        self.ui.consumables_btn.configure(command=self.labeling_manager.on_label_consumables)
        self.ui.jokers_btn.configure(command=self.labeling_manager.on_label_jokers)
    
    def _bind_labeling_shortcuts(self):
        """Bind keyboard shortcuts for data labeling"""
        root = self.ui.root
        root.bind('<KeyPress-c>', lambda e: self.labeling_manager.save_current_label())
        root.bind('<KeyPress-C>', lambda e: self.labeling_manager.save_current_label())
        root.bind('<KeyPress-x>', lambda e: self.labeling_manager.on_skip_card())
        root.bind('<KeyPress-X>', lambda e: self.labeling_manager.on_skip_card())
        root.bind('<KeyPress-q>', lambda e: self.labeling_manager.on_prev_card())
        root.bind('<KeyPress-Q>', lambda e: self.labeling_manager.on_prev_card())
        root.bind('<KeyPress-e>', lambda e: self.labeling_manager.on_next_card())
        root.bind('<KeyPress-E>', lambda e: self.labeling_manager.on_next_card())
        root.bind('<BackSpace>', lambda e: self.labeling_manager.on_label_not_card())
    
    def _unbind_labeling_shortcuts(self):
        """Unbind keyboard shortcuts"""
        root = self.ui.root
        shortcuts = ['<KeyPress-c>', '<KeyPress-C>', '<KeyPress-x>', '<KeyPress-X>',
                    '<KeyPress-q>', '<KeyPress-Q>', '<KeyPress-e>', '<KeyPress-E>', '<BackSpace>']
        for shortcut in shortcuts:
            root.unbind(shortcut)
    
    def _show_bottom_buttons(self):
        """Show bottom buttons"""
        if hasattr(self.ui, 'button_frame'):
            self.ui.button_frame.grid()
    
    def _hide_bottom_buttons(self):
        """Hide bottom buttons"""
        if hasattr(self.ui, 'button_frame'):
            self.ui.button_frame.grid_remove()
    
    def _load_suits_for_labeling(self):
        """Load suit sprites for data labeling mode"""
        try:
            suits_config = self.card_order_config.get('suits', {})
            if not suits_config:
                return
            
            sprite_sheet_name = suits_config['sprite_sheet']
            
            # Load suit sprites
            try:
                # Check if sprite sheet exists
                sheet_names = self.sprite_loader.get_sheet_names()
                print(f"Available sheets: {sheet_names}")
                print(f"Looking for: {sprite_sheet_name}")
                
                if sprite_sheet_name not in sheet_names:
                    print(f"Warning: Could not find suits sheet: {sprite_sheet_name}")
                    # Try to find a suits sheet by name matching
                    suits_sheets = [name for name in sheet_names if 'suit' in name.lower()]
                    if suits_sheets:
                        sprite_sheet_name = suits_sheets[0]
                        print(f"Using alternative suits sheet: {sprite_sheet_name}")
                    else:
                        return
                
                # Initialize suits storage
                if not hasattr(self.ui, 'suit_sprites'):
                    self.ui.suit_sprites = {}
                
                suit_order = suits_config['order']  # ["S", "H", "C", "D"]
                suit_indices = suits_config['indices']  # [3, 0, 1, 2]
                
                # Load each suit sprite
                for suit_name, suit_idx in zip(suit_order, suit_indices):
                    suit_sprite = self.sprite_loader.get_sprite(sprite_sheet_name, suit_idx)
                    if suit_sprite:
                        # Resize to match card dimensions
                        suit_sprite = suit_sprite.resize((71, 95), Image.Resampling.LANCZOS)
                        self.ui.suit_sprites[suit_name] = suit_sprite
                
                # Display suits on canvas
                self._display_suits()
                
            except Exception as e:
                print(f"Warning: Could not load suit sprites: {e}")
        
        except Exception as e:
            print(f"Error loading suits for labeling: {e}")
    
    def _display_suits(self):
        """Display suit symbols on the suits canvas with proper card-like spacing"""
        if not hasattr(self.ui, 'suit_sprites') or not self.ui.suit_sprites:
            return
        
        # Clear existing suits
        if hasattr(self.ui, 'suit_img_ids'):
            for img_id in self.ui.suit_img_ids:
                self.ui.suits_canvas.delete(img_id)
        
        self.ui.suit_img_ids = []
        
        # Calculate canvas dimensions
        num_suits = len(self.ui.suit_sprites)
        canvas_width = 71 + 20  # Card width + padding
        canvas_height = num_suits * (95 + 2) - 2 + 20  # Cards + spacing
        
        self.ui.suits_canvas.configure(width=canvas_width, height=canvas_height)
        
        suit_order = ["S", "H", "C", "D"]  # Display order
        
        for i, suit_name in enumerate(suit_order):
            if suit_name in self.ui.suit_sprites:
                suit_sprite = self.ui.suit_sprites[suit_name]
                
                # Convert to PhotoImage
                from PIL import ImageTk
                suit_photo = ImageTk.PhotoImage(suit_sprite)
                
                # Calculate position
                x = canvas_width // 2
                y = 10 + i * (95 + 2) + 95 // 2
                
                # Create image on canvas
                img_id = self.ui.suits_canvas.create_image(x, y, image=suit_photo, anchor=tk.CENTER)
                self.ui.suit_img_ids.append(img_id)
                
                # Store reference to prevent garbage collection
                setattr(self.ui.suits_canvas, f'suit_photo_{i}', suit_photo)
                
                # Bind click event for suit selection
                self.ui.suits_canvas.tag_bind(img_id, '<Button-1>', 
                                            lambda e, s=suit_name: self._on_suit_click(s))
                self.ui.suits_canvas.tag_bind(img_id, '<Enter>', 
                                            lambda e: self.ui.suits_canvas.configure(cursor='hand2'))
                self.ui.suits_canvas.tag_bind(img_id, '<Leave>', 
                                            lambda e: self.ui.suits_canvas.configure(cursor=''))
    
    def _on_suit_click(self, suit_name):
        """Handle suit symbol click for suit-only labeling"""
        suit_mapping = {"S": "s", "H": "h", "C": "c", "D": "d"}
        suit_code = suit_mapping.get(suit_name, suit_name.lower())
        
        self.labeling_manager.selected_card_class = f"suit_only_{suit_code}"
        
        # Update matched card display
        suit_display_names = {"S": "Spades", "H": "Hearts", "C": "Clubs", "D": "Diamonds"}
        display_name = suit_display_names.get(suit_name, suit_name)
        self.card_display_manager.display_suit_in_matched_display(display_name, "Selected")
    
    def get_current_mode(self):
        """Get the current application mode"""
        return self.current_mode