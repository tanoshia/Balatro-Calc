#!/usr/bin/env python3
"""
Nebulatro - Balatro Card Order Tracker
Main application orchestrator
"""

import tkinter as tk
from tkinter import messagebox
import json
from pathlib import Path

from src.utils import SpriteLoader
from src.ui import UIComponents, LayoutManager
from src.managers import CardManager, ModifierManager, DesignManager
from src.vision import CardRecognizer, ScreenCapture


class BalatroTracker:
    """Main application class - orchestrates all components"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Nebulatro")
        
        # Configuration
        self.card_display_width = 71
        self.card_display_height = 95
        self.card_spacing = 2
        self.bg_color = '#2b2b2b'
        self.canvas_bg = '#1e1e1e'
        
        # Set minimum window size
        min_width = int(13 * self.card_display_width - 12 * (self.card_display_width * 0.55)) + 15
        min_height = 710
        self.root.minsize(min_width, min_height)
        
        # Load configuration
        self.card_order_config = self._load_config()
        
        # Data Labeling Layout Configuration (loaded from config or defaults)
        layout_config = self.card_order_config.get('data_labeling_layout', {}) if self.card_order_config else {}
        self.suits_column_width = layout_config.get('suits_column_width', 100)
        self.cards_column_min_width = layout_config.get('cards_column_min_width', 800)
        self.cards_column_max_width = layout_config.get('cards_column_max_width', 1200)
        
        # Initialize sprite loader
        self.sprite_loader = SpriteLoader()
        
        # Initialize vision system
        self.screen_capture = ScreenCapture()
        self.card_recognizer = CardRecognizer(self.sprite_loader)
        
        # Initialize UI components
        self.ui = UIComponents(self.root, self.bg_color, self.canvas_bg)
        self.ui.set_app_icon()
        self.ui.setup_main_layout(
            self.card_display_width, 
            self.card_display_height,
            self._on_modifier_filter_change,
            self._on_card_design_click,
            self._on_clear,
            self._on_undo,
            self._on_save,
            self._on_capture_hand,
            self._on_mode_change
        )
        
        # Initialize managers
        self._setup_managers()
        
        # Initialize data labeling
        self._setup_data_labeling()
        
        # Load initial content
        self._load_initial_content()
        
        # Setup event handlers
        self.root.bind('<Configure>', self._on_window_resize)
        self.root.after(100, self._recalculate_positions)
    
    def _setup_managers(self):
        """Initialize all manager components"""
        # Card manager
        self.card_manager = CardManager(
            self.sprite_loader,
            self.card_order_config,
            self.ui.card_grid_canvas,
            self.ui.order_canvas,
            self.ui.order_frame,
            self.card_display_width,
            self.card_display_height,
            self.card_spacing,
            self.bg_color
        )
        self.card_manager.set_card_click_handler(self._on_card_click)
        
        # Modifier manager
        self.modifier_manager = ModifierManager(
            self.sprite_loader,
            self.card_order_config,
            self.ui.modifiers_canvas,
            self.card_display_width,
            self.card_display_height,
            self.card_spacing,
            self.bg_color
        )
        self.modifier_manager.set_modifier_change_handler(self._on_modifier_change)
        
        # Design manager
        self.design_manager = DesignManager(
            self.root,
            self.sprite_loader,
            self.bg_color,
            self.ui.card_contrast,
            self.ui.face_card_collabs
        )
        self.design_manager.set_design_change_handler(self._on_design_change)
        
        # Layout manager
        self.layout_manager = LayoutManager(
            self.ui.card_grid_canvas,
            self.ui.modifiers_canvas,
            self.card_display_width,
            self.card_display_height,
            self.card_spacing
        )
    
    def _load_initial_content(self):
        """Load modifiers and cards"""
        # Load modifiers
        filter_mode = self.ui.modifier_filter.get()
        self.modifier_manager.load_modifiers(filter_mode)
        
        # Load cards
        use_high_contrast = self.ui.card_contrast.get() == "High Contrast"
        canvas_width, canvas_height = self.card_manager.load_cards(use_high_contrast, self.design_manager)
        
        # Auto-size window
        self.layout_manager.auto_size_window(self.root, canvas_width, canvas_height)
    
    # Event Handlers
    
    def _on_card_click(self, card_name):
        """Handle card click - behavior depends on current mode"""
        current_mode = self.ui.app_mode.get()
        
        if current_mode == "Manual Tracking":
            self._handle_tracking_card_click(card_name)
        elif current_mode == "Data Labeling":
            self._handle_labeling_card_click(card_name)
    
    def _handle_tracking_card_click(self, card_name):
        """Handle card click in manual tracking mode"""
        if card_name not in self.card_manager.base_card_sprites:
            return
        
        base_sprite = self.card_manager.base_card_sprites[card_name]
        card_face = self.card_manager.card_faces.get(card_name)
        
        # Apply modifiers
        final_sprite = self.modifier_manager.apply_modifiers_to_card(base_sprite, card_face)
        modifiers_applied = self.modifier_manager.get_selected_modifiers()
        
        # Add to order
        self.card_manager.add_card_to_order(card_name, final_sprite, modifiers_applied)
    
    def _handle_labeling_card_click(self, card_name):
        """Handle card click in data labeling mode"""
        if not self.labeling_cards or self.current_labeling_index >= len(self.labeling_cards):
            messagebox.showwarning("No Card", "No card loaded for labeling")
            return
        
        # Get the sprite index for this card
        card_order = self.card_order_config['playing_cards_order']['sprite_sheet_mapping']['order']
        
        # Find the sprite index for this card name
        sprite_idx = None
        for i, name in enumerate(self.card_manager.base_card_sprites.keys()):
            if name == card_name:
                sprite_idx = card_order[i]
                break
        
        if sprite_idx is not None:
            self.selected_card_class = sprite_idx
            
            # Get card info for display
            suits = ["Hearts", "Clubs", "Diamonds", "Spades"]
            ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
            suit_idx = sprite_idx // 13
            rank_idx = sprite_idx % 13
            
            if suit_idx < len(suits) and rank_idx < len(ranks):
                card_desc = f"{ranks[rank_idx]} of {suits[suit_idx]}"
            else:
                card_desc = f"Card {sprite_idx}"
            
            # Show current modifiers if any
            modifiers = self.modifier_manager.get_selected_modifiers()
            modifier_text = ""
            if modifiers:
                if isinstance(modifiers, dict):
                    active_mods = [k for k, v in modifiers.items() if v]
                elif isinstance(modifiers, list):
                    active_mods = [str(m) for m in modifiers if m]
                else:
                    active_mods = [str(modifiers)]
                
                if active_mods:
                    modifier_text = f"\nWith modifiers: {', '.join(active_mods)}"
            
            messagebox.showinfo("Card Selected", 
                               f"Selected: {card_desc}\nClass: {sprite_idx}{modifier_text}\n\nClick 'Save Label' to confirm")
        else:
            messagebox.showerror("Error", f"Could not find sprite index for {card_name}")
    
    def _on_modifier_change(self):
        """Handle modifier selection change - refresh card display"""
        self.card_manager.refresh_card_display(self.modifier_manager)
    
    def _on_modifier_filter_change(self, event=None):
        """Handle modifier filter change"""
        filter_value = self.ui.modifier_filter.get()
        self.modifier_manager.clear_modifiers()
        self.modifier_manager.load_modifiers(filter_value)
        self._recalculate_positions()
    
    def _on_card_design_click(self):
        """Open card design popup"""
        self.design_manager.open_design_popup()
    
    def _on_design_change(self):
        """Handle design change - reload cards"""
        self.card_manager.clear_cards()
        use_high_contrast = self.ui.card_contrast.get() == "High Contrast"
        self.card_manager.load_cards(use_high_contrast, self.design_manager)
    
    def _on_clear(self):
        """Clear card order or selection"""
        current_mode = self.ui.app_mode.get()
        
        if current_mode == "Manual Tracking":
            self.card_manager.clear_order()
        elif current_mode == "Data Labeling":
            self.selected_card_class = None
            messagebox.showinfo("Cleared", "Card selection cleared")
    
    def _on_undo(self):
        """Undo last card or go to previous card"""
        current_mode = self.ui.app_mode.get()
        
        if current_mode == "Manual Tracking":
            self.card_manager.undo_last()
        elif current_mode == "Data Labeling":
            self._on_prev_labeling_card()
    
    def _on_save(self):
        """Save card order or label current card"""
        current_mode = self.ui.app_mode.get()
        
        if current_mode == "Manual Tracking":
            success, message = self.card_manager.save_order()
            title = "Saved!" if success else "Error"
            messagebox.showinfo(title, message)
        elif current_mode == "Data Labeling":
            self._save_current_label()
    
    def _save_current_label(self):
        """Save the current card label"""
        if self.selected_card_class is None:
            messagebox.showwarning("No Selection", "Please click on a card or select a special label first")
            return
        
        if not self.labeling_cards or self.current_labeling_index >= len(self.labeling_cards):
            messagebox.showwarning("No Card", "No card loaded for labeling")
            return
        
        try:
            card_path = self.labeling_cards[self.current_labeling_index]
            
            if (self.selected_card_class in ["not_card", "suit_only"] or 
                (isinstance(self.selected_card_class, str) and self.selected_card_class.startswith("suit_only_"))):
                # Handle special labels
                output_path = self._save_special_label(card_path, self.selected_card_class)
                if self.selected_card_class == "not_card":
                    label_text = "Not a Card"
                elif self.selected_card_class.startswith("suit_only_"):
                    suit_name = self.selected_card_class.replace("suit_only_", "").title()
                    label_text = f"Suit Only ({suit_name})"
                else:
                    label_text = "Suit Only"
            else:
                # Handle regular card labels
                from label_single_card import save_labeled_card
                output_path = save_labeled_card(card_path, self.selected_card_class)
                label_text = f"Class {self.selected_card_class}"
            
            messagebox.showinfo("Saved", f"Card labeled as: {label_text}\n"
                                        f"Saved to: {output_path}")
            
            # Move to next card
            self._on_next_labeling_card()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save label: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_special_label(self, card_path, label_type):
        """Save special labels (not_card, suit_only, suit_only_*)"""
        import cv2
        from pathlib import Path
        
        # Create special label directory
        if label_type.startswith("suit_only_"):
            # Create suit-specific directory
            special_dir = Path("training_data/processed") / label_type
        else:
            special_dir = Path("training_data/processed") / label_type
        special_dir.mkdir(parents=True, exist_ok=True)
        
        # Load and process image
        image = cv2.imread(str(card_path))
        h, w = image.shape[:2]
        corner_h = int(h * 0.35)
        corner_w = int(w * 0.35)
        corner = image[:corner_h, :corner_w]
        
        # Save corner region
        output_path = special_dir / f"{card_path.stem}_corner.png"
        cv2.imwrite(str(output_path), corner)
        
        # Also save full image for reference
        ref_dir = special_dir / "reference"
        ref_dir.mkdir(exist_ok=True)
        ref_path = ref_dir / f"{card_path.stem}_full.png"
        cv2.imwrite(str(ref_path), image)
        
        return output_path
    
    def _setup_suits_display(self):
        """Setup suits display for data labeling mode"""
        if self.suits_canvas is not None:
            return  # Already set up
        
        # Create suits canvas directly in the main frame, positioned to the left
        parent = self.ui.card_grid_canvas.master
        
        # Create suits canvas
        self.suits_canvas = tk.Canvas(parent, bg=self.bg_color, 
                                     highlightthickness=0, width=80)
        
        # Position suits to the left of cards using grid
        # Get current card grid position
        card_grid_info = self.ui.card_grid_canvas.grid_info()
        card_row = card_grid_info.get('row', 2)
        
        # Place suits in same row, column 0, and move cards to column 1
        self.suits_canvas.grid(row=card_row, column=0, sticky='ne', padx=(0, 5), pady=10)
        self.ui.card_grid_canvas.grid(row=card_row, column=1, pady=10)
        
        # Load and display suits
        self._load_suits_sprites()
    
    def _load_suits_sprites(self):
        """Load and display suit sprites"""
        try:
            from PIL import Image, ImageTk
            import os
            
            # Load suits sprite sheet
            suits_path = "assets/1x4 Suits.png"
            if not os.path.exists(suits_path):
                print(f"Warning: Suits sprite sheet not found at {suits_path}")
                return
            
            suits_img = Image.open(suits_path).convert('RGBA')
            
            # Calculate suit dimensions (1x4 grid)
            suit_width = suits_img.width
            suit_height = suits_img.height // 4
            
            # Get display order from config
            suits_config = self.card_order_config.get('suits_order', {})
            display_order = suits_config.get('display_order', [3, 0, 1, 2])  # Spades, Hearts, Clubs, Diamonds
            
            # Extract and display each suit
            for i, suit_idx in enumerate(display_order):
                # Extract suit sprite
                top = suit_idx * suit_height
                suit_sprite = suits_img.crop((0, top, suit_width, top + suit_height))
                
                # Resize to match card height
                target_height = 60  # Smaller than cards
                aspect_ratio = suit_sprite.width / suit_sprite.height
                target_width = int(target_height * aspect_ratio)
                suit_sprite = suit_sprite.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                suit_photo = ImageTk.PhotoImage(suit_sprite)
                
                # Position on canvas
                x = target_width // 2 + 10
                y = i * (target_height + 10) + target_height // 2 + 10
                
                # Create clickable suit
                suit_id = self.suits_canvas.create_image(x, y, image=suit_photo)
                
                # Store reference and bind click
                suit_name = ['Spades', 'Hearts', 'Clubs', 'Diamonds'][i]
                self.suits_images[suit_id] = {
                    'photo': suit_photo,
                    'suit_name': suit_name,
                    'suit_idx': suit_idx
                }
                
                # Bind click event for suit-only labeling
                self.suits_canvas.tag_bind(suit_id, '<Button-1>', 
                                         lambda e, suit=suit_name: self._on_suit_click(suit))
                self.suits_canvas.tag_bind(suit_id, '<Enter>', 
                                         lambda e: self.suits_canvas.configure(cursor='hand2'))
                self.suits_canvas.tag_bind(suit_id, '<Leave>', 
                                         lambda e: self.suits_canvas.configure(cursor=''))
            
            # Update canvas scroll region
            self.suits_canvas.configure(scrollregion=self.suits_canvas.bbox("all"))
            
        except Exception as e:
            print(f"Error loading suits: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_suit_click(self, suit_name):
        """Handle suit click for suit-only labeling"""
        if not self.labeling_cards or self.current_labeling_index >= len(self.labeling_cards):
            messagebox.showwarning("No Card", "No card loaded for labeling")
            return
        
        # Set special suit-only class
        self.selected_card_class = f"suit_only_{suit_name.lower()}"
        
        # Show current modifiers if any
        modifiers = self.modifier_manager.get_selected_modifiers()
        modifier_text = ""
        if modifiers:
            if isinstance(modifiers, dict):
                active_mods = [k for k, v in modifiers.items() if v]
            elif isinstance(modifiers, list):
                active_mods = [str(m) for m in modifiers if m]
            else:
                active_mods = [str(modifiers)]
            
            if active_mods:
                modifier_text = f"\nWith modifiers: {', '.join(active_mods)}"
        
        messagebox.showinfo("Suit Selected", 
                           f"Selected: {suit_name} (Suit Only){modifier_text}\n\nClick 'Save Label' to confirm")
    
    def _on_mode_change(self, event=None):
        """Handle mode change between Manual Tracking and Data Labeling"""
        current_mode = self.ui.app_mode.get()
        
        # Update title, buttons, and order label
        self.ui.update_title_for_mode(current_mode)
        self.ui.update_buttons_for_mode(current_mode)
        self.ui.update_order_label_for_mode(current_mode)
        
        if current_mode == "Manual Tracking":
            # Show order list, hide labeling area and suits
            if hasattr(self.ui, 'labeling_frame'):
                self.ui.labeling_frame.grid_remove()
            if hasattr(self.ui, 'labeling_nav_frame'):
                self.ui.labeling_nav_frame.grid_remove()
            if hasattr(self.ui, 'labeling_image_frame'):
                self.ui.labeling_image_frame.grid_remove()
            if self.suits_canvas:
                self.suits_canvas.grid_remove()
            
            # Restore all UI elements back to column 0 (original layout)
            main_frame = self.ui.modifiers_canvas.master
            
            # Restore title/filters to column 0
            title_frame_info = main_frame.grid_slaves(row=0)[0] if main_frame.grid_slaves(row=0) else None
            if title_frame_info:
                title_frame_info.grid(row=0, column=0, pady=10, sticky=(tk.W, tk.E))
            
            # Restore modifiers to column 0
            self.ui.modifiers_canvas.grid(row=1, column=0, pady=(0, 5))
            
            # Restore card grid to column 0
            self.ui.card_grid_canvas.grid(row=2, column=0, pady=10)
            
            # Restore separator to column 0
            separator_widgets = [w for w in main_frame.grid_slaves(row=3) if isinstance(w, tk.ttk.Separator)]
            if separator_widgets:
                separator_widgets[0].grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
            
            # Restore order label to column 0
            order_labels = [w for w in main_frame.grid_slaves(row=4) if isinstance(w, tk.Label)]
            if order_labels:
                order_labels[0].grid(row=4, column=0, sticky=tk.W)
            
            # Restore buttons to column 0 (check both row 6 and 7)
            button_frames = ([w for w in main_frame.grid_slaves(row=7) if isinstance(w, tk.ttk.Frame)] or 
                           [w for w in main_frame.grid_slaves(row=6) if isinstance(w, tk.ttk.Frame)])
            if button_frames:
                button_frames[0].grid(row=6, column=0, pady=10)
            
            # Restore original column configuration
            main_frame.columnconfigure(0, weight=1, minsize=0)
            main_frame.columnconfigure(1, weight=0, minsize=0)
            
            self.ui.order_frame.grid()
        elif current_mode == "Data Labeling":
            # Hide order list, show labeling area
            self.ui.order_frame.grid_remove()
            
            # Setup suits display and move cards to column 1
            if not hasattr(self.ui, 'labeling_controls_created'):
                # Create labeling controls directly in main frame at column 1
                main_frame = self.ui.modifiers_canvas.master
                
                # Create navigation buttons directly in main frame
                nav_frame = tk.Frame(main_frame, bg=self.bg_color)
                nav_frame.grid(row=5, column=1, sticky='w', pady=(10, 5))
                
                self.ui.prev_card_btn = tk.Button(nav_frame, text="← Previous", 
                                                 state=tk.DISABLED, width=10,
                                                 command=self._on_prev_labeling_card)
                self.ui.prev_card_btn.pack(side=tk.LEFT, padx=5)
                
                self.ui.next_card_btn = tk.Button(nav_frame, text="Next →", 
                                                 state=tk.DISABLED, width=10,
                                                 command=self._on_next_labeling_card)
                self.ui.next_card_btn.pack(side=tk.LEFT, padx=5)
                
                self.ui.skip_card_btn = tk.Button(nav_frame, text="Skip", 
                                                 state=tk.DISABLED, width=10,
                                                 command=self._on_skip_labeling_card)
                self.ui.skip_card_btn.pack(side=tk.LEFT, padx=5)
                
                self.ui.not_card_btn = tk.Button(nav_frame, text="Not a Card", 
                                                state=tk.DISABLED, width=12,
                                                bg='#f44336', fg='white',
                                                command=self._on_label_not_card)
                self.ui.not_card_btn.pack(side=tk.LEFT, padx=10)
                
                # Create image display directly in main frame
                image_frame = tk.Frame(main_frame, bg=self.bg_color, relief=tk.RAISED, bd=2)
                image_frame.grid(row=6, column=1, sticky='w', pady=10)
                
                # Title for labeling area
                label_title = tk.Label(image_frame, text="Card to Label", 
                                      font=('Arial', 12, 'bold'),
                                      bg=self.bg_color, fg='white')
                label_title.pack(pady=(10, 5))
                
                # Image display
                self.ui.label_image_display = tk.Label(image_frame, 
                                                      text="No card loaded\n\nClick 'Load Cards' to start labeling", 
                                                      font=('Arial', 10),
                                                      bg=self.bg_color, fg='#cccccc')
                self.ui.label_image_display.pack(padx=20, pady=10)
                
                # Card info
                self.ui.label_info = tk.Label(image_frame, text="", 
                                             font=('Arial', 9),
                                             bg=self.bg_color, fg='#aaaaaa')
                self.ui.label_info.pack(pady=(0, 10))
                
                # Store references
                self.ui.labeling_nav_frame = nav_frame
                self.ui.labeling_image_frame = image_frame
                self.ui.labeling_controls_created = True
                
                # Setup suits display for data labeling
                self._setup_suits_display()
            else:
                # Show existing labeling controls
                if hasattr(self.ui, 'labeling_nav_frame'):
                    self.ui.labeling_nav_frame.grid(row=5, column=1, sticky='w', pady=(10, 5))
                if hasattr(self.ui, 'labeling_image_frame'):
                    self.ui.labeling_image_frame.grid(row=6, column=1, sticky='w', pady=10)
                
                # Show suits and reposition cards
                if self.suits_canvas:
                    self.suits_canvas.grid(row=2, column=0, sticky='ne', padx=(0, 5), pady=10)
                self.ui.card_grid_canvas.grid(row=2, column=1, pady=10)
            
            # Keep everything else in column 1 (right column) - no column spanning needed
            # All other elements stay in their original positions but in column 1
            main_frame = self.ui.modifiers_canvas.master
            
            # Move title/filters to column 1
            title_frame_info = main_frame.grid_slaves(row=0)[0] if main_frame.grid_slaves(row=0) else None
            if title_frame_info:
                title_frame_info.grid(row=0, column=1, pady=10, sticky=(tk.W, tk.E))
            
            # Move modifiers to column 1
            self.ui.modifiers_canvas.grid(row=1, column=1, pady=(0, 5))
            
            # Move separator to column 1
            separator_widgets = [w for w in main_frame.grid_slaves(row=3) if isinstance(w, tk.ttk.Separator)]
            if separator_widgets:
                separator_widgets[0].grid(row=3, column=1, sticky=(tk.W, tk.E), pady=10)
            
            # Move order label to column 1
            order_labels = [w for w in main_frame.grid_slaves(row=4) if isinstance(w, tk.Label)]
            if order_labels:
                order_labels[0].grid(row=4, column=1, sticky=tk.W)
            
            # Labeling controls are now created directly in the main frame above
            
            # Move buttons to column 1 (after image display)
            # Find the button frame (it's a ttk.Frame at row 6)
            button_frames = [w for w in main_frame.grid_slaves(row=6) if isinstance(w, tk.ttk.Frame)]
            if button_frames:
                button_frames[0].grid(row=7, column=1, pady=10, sticky='w')
            
            # Configure column weights and constraints for data labeling layout
            main_frame.columnconfigure(0, weight=0, minsize=self.suits_column_width)  # Fixed width for suits
            main_frame.columnconfigure(1, weight=1, minsize=self.cards_column_min_width)  # Expandable cards column
    
    def _on_capture_hand(self):
        """Capture and recognize cards from game screen OR load cards for labeling"""
        current_mode = self.ui.app_mode.get()
        
        if current_mode == "Manual Tracking":
            self._capture_hand_for_tracking()
        elif current_mode == "Data Labeling":
            self._load_cards_for_labeling()
    
    def _capture_hand_for_tracking(self):
        """Capture and recognize cards for manual tracking"""
        try:
            from tkinter import filedialog
            
            filepath = filedialog.askopenfilename(
                title="Select Balatro Screenshot",
                filetypes=[("Image files", "*.png *.jpg *.jpeg"), ("All files", "*.*")]
            )
            
            if not filepath:
                return
            
            # Load the image
            screenshot = self.screen_capture.capture_from_file(filepath)
            
            # Extract card region
            card_region = self.screen_capture.get_card_region(screenshot)
            
            if card_region is None:
                messagebox.showerror("Error", "Could not extract card region from image")
                return
            
            # Recognize cards
            recognized_cards = self.card_recognizer.recognize_hand(card_region)
            
            if not recognized_cards:
                messagebox.showinfo("No Cards Found", "No cards were detected in the image")
                return
            
            # Add recognized cards to order
            for card_info in recognized_cards:
                card_idx = card_info['index']
                
                # Get the card sprite
                if card_idx < len(self.card_manager.base_card_sprites):
                    card_names = list(self.card_manager.base_card_sprites.keys())
                    if card_idx < len(card_names):
                        card_name = card_names[card_idx]
                        
                        # Get sprites
                        base_sprite = self.card_manager.base_card_sprites[card_name]
                        card_face = self.card_manager.card_faces.get(card_name)
                        
                        # Apply modifiers (if detected)
                        final_sprite = self.modifier_manager.apply_modifiers_to_card(base_sprite, card_face)
                        modifiers_applied = self.modifier_manager.get_selected_modifiers()
                        
                        # Add to order
                        self.card_manager.add_card_to_order(card_name, final_sprite, modifiers_applied)
            
            messagebox.showinfo("Success", f"Added {len(recognized_cards)} cards to order")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture hand: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_cards_for_labeling(self):
        """Load cards for data labeling"""
        from tkinter import filedialog
        
        directory = filedialog.askdirectory(
            title="Select directory with card images to label",
            initialdir="training_data/debug_cards"
        )
        
        if not directory:
            return
        
        # Load card images
        directory = Path(directory)
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            image_files.extend(directory.glob(ext))
        
        # Filter out preview/processed files
        image_files = [f for f in image_files if 'preview' not in f.name.lower() 
                      and 'comparison' not in f.name.lower()
                      and 'corner' not in f.name.lower()
                      and 'region' not in f.name.lower()]
        
        if not image_files:
            messagebox.showwarning("No Cards", f"No card images found in {directory}")
            return
        
        self.labeling_cards = sorted(image_files)
        self.current_labeling_index = 0
        
        # Enable navigation buttons
        self.ui.prev_card_btn.configure(state=tk.NORMAL)
        self.ui.next_card_btn.configure(state=tk.NORMAL)
        self.ui.skip_card_btn.configure(state=tk.NORMAL)
        self.ui.not_card_btn.configure(state=tk.NORMAL)
        self.ui.suit_only_btn.configure(state=tk.NORMAL)
        
        # Load first card
        self._load_current_labeling_card()
        
        messagebox.showinfo("Cards Loaded", f"Loaded {len(self.labeling_cards)} cards for labeling")
    
    def _load_current_labeling_card(self):
        """Load the current card for labeling"""
        if not self.labeling_cards or self.current_labeling_index >= len(self.labeling_cards):
            return
        
        card_path = self.labeling_cards[self.current_labeling_index]
        
        try:
            import cv2
            from PIL import ImageTk
            
            # Load image
            image = cv2.imread(str(card_path))
            if image is None:
                raise ValueError("Could not load image")
            
            # Show full image for labeling (not just corner)
            # Convert to PIL for display
            full_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            from PIL import Image
            full_pil = Image.fromarray(full_rgb)
            
            # Calculate size based on window size and scale down large images
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            
            # Use percentage of window size for max dimensions
            max_width = min(int(window_width * 0.25), 350)  # 25% of window width, max 350px
            max_height = min(int(window_height * 0.4), 450)  # 40% of window height, max 450px
            
            # Ensure minimum size
            max_width = max(max_width, 200)
            max_height = max(max_height, 250)
            
            img_width, img_height = full_pil.size
            
            # Scale based on the largest dimension to fit within bounds
            if img_width > max_width or img_height > max_height:
                scale_w = max_width / img_width
                scale_h = max_height / img_height
                scale = min(scale_w, scale_h)
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                full_pil = full_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                # Image is already small enough, use original size
                new_width, new_height = img_width, img_height
            
            # Convert to PhotoImage
            self.current_labeling_image = ImageTk.PhotoImage(full_pil)
            
            # Update display - configure both image and compound to ensure proper display
            self.ui.label_image_display.configure(
                image=self.current_labeling_image, 
                text="",
                compound=tk.CENTER,
                width=new_width,
                height=new_height
            )
            
            # Store reference to prevent garbage collection
            self.ui.label_image_display.image = self.current_labeling_image
            
            # Update info
            info_text = (f"File: {card_path.name}\n"
                        f"Card {self.current_labeling_index + 1} of {len(self.labeling_cards)}\n"
                        f"Full image shown (model trains on top-left corner)")
            self.ui.label_info.configure(text=info_text)
            
            # Reset selection
            self.selected_card_class = None
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load card: {e}")
    
    def _on_prev_labeling_card(self):
        """Go to previous labeling card"""
        if self.current_labeling_index > 0:
            self.current_labeling_index -= 1
            self._load_current_labeling_card()
    
    def _on_next_labeling_card(self):
        """Go to next labeling card"""
        if self.current_labeling_index < len(self.labeling_cards) - 1:
            self.current_labeling_index += 1
            self._load_current_labeling_card()
    
    def _on_skip_labeling_card(self):
        """Skip current labeling card"""
        self._on_next_labeling_card()
    
    def _on_label_not_card(self):
        """Label current image as 'not a card'"""
        self.selected_card_class = "not_card"
        messagebox.showinfo("Not a Card", "Marked as 'Not a Card'\n\nClick 'Save Label' to confirm")
    
    def _on_label_suit_only(self):
        """Label current image as 'suit only' (partial card)"""
        self.selected_card_class = "suit_only"
        messagebox.showinfo("Suit Only", "Marked as 'Suit Only'\n\nClick 'Save Label' to confirm")
    
    def _on_window_resize(self, event):
        """Handle window resize"""
        if event.widget != self.root:
            return
        self._recalculate_positions()
        
        # Update labeling image size if in data labeling mode
        current_mode = self.ui.app_mode.get()
        if current_mode == "Data Labeling" and hasattr(self, 'labeling_cards') and self.labeling_cards:
            # Reload current image with new size
            self.root.after(100, self._reload_current_image_size)  # Small delay to let resize complete
    
    def _reload_current_image_size(self):
        """Reload current labeling image with updated size"""
        if (hasattr(self, 'labeling_cards') and self.labeling_cards and 
            self.current_labeling_index < len(self.labeling_cards)):
            self._load_current_labeling_card()
    

    
    def _recalculate_positions(self):
        """Recalculate all positions"""
        self.layout_manager.recalculate_card_positions(
            self.card_manager.card_positions,
            self.card_manager.card_img_ids
        )
        self.layout_manager.recalculate_modifier_positions(
            self.modifier_manager.modifier_positions,
            self.modifier_manager.modifier_img_ids,
            self.modifier_manager.modifier_types,
            self.modifier_manager.modifier_display_widths
        )
    
    # Utility Methods
    
    def _setup_data_labeling(self):
        """Initialize data labeling functionality"""
        self.labeling_cards = []
        self.current_labeling_index = 0
        self.current_labeling_image = None
        self.selected_card_class = None
        self.suits_canvas = None
        self.suits_images = {}
        
    def _load_config(self):
        """Load card order configuration"""
        config_path = Path("config/card_order_config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load card order config: {e}")
        return None


def main():
    root = tk.Tk()
    app = BalatroTracker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
