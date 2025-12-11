#!/usr/bin/env python3
"""
GUI Card Labeler - Visual card labeling using Balatro tracker interface
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageTk

# Import the existing UI components
sys.path.insert(0, str(Path(__file__).parent))
from src.managers.card_manager import CardManager
from src.utils.sprite_loader import SpriteLoader


class CardLabelerGUI:
    """GUI for labeling cards using visual card selection"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Balatro Card Labeler")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        # Initialize card system
        self.sprite_loader = SpriteLoader()
        
        # Load card order configuration
        import json
        with open('config/card_order_config.json', 'r') as f:
            self.card_config = json.load(f)
        
        # Get card order
        self.card_order = self.card_config['playing_cards_order']['sprite_sheet_mapping']['order']
        
        # Current card being labeled
        self.current_card_path = None
        self.current_card_image = None
        self.selected_class = None
        self.card_queue = []
        self.current_index = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the GUI layout"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Card being labeled
        left_frame = tk.Frame(main_frame, bg='#2b2b2b')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        # Card display area
        self.setup_card_display(left_frame)
        
        # Right side - Card selection interface
        right_frame = tk.Frame(main_frame, bg='#2b2b2b')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Card selection area
        self.setup_card_selection(right_frame)
        
        # Bottom controls
        self.setup_controls(main_frame)
        
    def setup_card_display(self, parent):
        """Setup the card display area"""
        # Title
        title_label = tk.Label(parent, text="Card to Label", 
                              font=('Arial', 16, 'bold'), 
                              fg='white', bg='#2b2b2b')
        title_label.pack(pady=(0, 10))
        
        # Card image display
        self.card_display_frame = tk.Frame(parent, bg='#2b2b2b', 
                                          relief=tk.RAISED, bd=2)
        self.card_display_frame.pack(pady=10)
        
        # Placeholder for card image
        self.card_image_label = tk.Label(self.card_display_frame, 
                                        text="No card loaded", 
                                        font=('Arial', 12),
                                        fg='white', bg='#2b2b2b',
                                        width=30, height=15)
        self.card_image_label.pack(padx=20, pady=20)
        
        # Card info
        self.card_info_label = tk.Label(parent, text="", 
                                       font=('Arial', 10),
                                       fg='#cccccc', bg='#2b2b2b')
        self.card_info_label.pack(pady=5)
        
        # Progress info
        self.progress_label = tk.Label(parent, text="", 
                                      font=('Arial', 10),
                                      fg='#cccccc', bg='#2b2b2b')
        self.progress_label.pack(pady=5)
        
    def setup_card_selection(self, parent):
        """Setup the card selection interface using existing card manager"""
        # Title
        title_label = tk.Label(parent, text="Click the matching card:", 
                              font=('Arial', 16, 'bold'), 
                              fg='white', bg='#2b2b2b')
        title_label.pack(pady=(0, 10))
        
        # Create canvas for cards (similar to main app)
        self.cards_canvas = tk.Canvas(parent, bg='#2b2b2b', 
                                     highlightthickness=0,
                                     height=400)
        self.cards_canvas.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Load and display all cards
        self.display_all_cards()
        
    def display_all_cards(self):
        """Display all 52 cards in a grid for selection"""
        # Clear canvas
        self.cards_canvas.delete("all")
        
        # Get card order from config
        card_order = self.card_order
        
        # Calculate grid layout
        cols = 13  # 13 ranks
        rows = 4   # 4 suits
        card_width = 60
        card_height = 80
        spacing_x = 5
        spacing_y = 5
        
        # Update canvas size
        canvas_width = cols * (card_width + spacing_x) - spacing_x + 20
        canvas_height = rows * (card_height + spacing_y) - spacing_y + 20
        self.cards_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Display cards
        self.card_buttons = {}
        for row in range(rows):
            for col in range(cols):
                display_pos = row * cols + col
                if display_pos < len(card_order):
                    sprite_idx = card_order[display_pos]
                    
                    # Get card sprite
                    card_sprite = self.sprite_loader.get_sprite('Playing Cards (High Contrast)', sprite_idx, composite_back=True)
                    if card_sprite:
                        # Resize for display
                        card_sprite = card_sprite.resize((card_width, card_height), Image.Resampling.LANCZOS)
                        card_photo = ImageTk.PhotoImage(card_sprite)
                        
                        # Calculate position
                        x = col * (card_width + spacing_x) + 10
                        y = row * (card_height + spacing_y) + 10
                        
                        # Create clickable card
                        card_id = self.cards_canvas.create_image(x, y, anchor=tk.NW, image=card_photo)
                        
                        # Store reference to prevent garbage collection
                        self.card_buttons[card_id] = {
                            'photo': card_photo,
                            'class_id': sprite_idx,
                            'display_pos': display_pos
                        }
                        
                        # Bind click event
                        self.cards_canvas.tag_bind(card_id, '<Button-1>', 
                                                  lambda e, class_id=sprite_idx: self.select_card(class_id))
                        self.cards_canvas.tag_bind(card_id, '<Enter>', 
                                                  lambda e, card_id=card_id: self.highlight_card(card_id, True))
                        self.cards_canvas.tag_bind(card_id, '<Leave>', 
                                                  lambda e, card_id=card_id: self.highlight_card(card_id, False))
        
    def highlight_card(self, card_id, highlight):
        """Highlight card on hover"""
        if highlight:
            self.cards_canvas.configure(cursor='hand2')
        else:
            self.cards_canvas.configure(cursor='')
    
    def select_card(self, class_id):
        """Handle card selection"""
        self.selected_class = class_id
        
        # Show selection feedback
        messagebox.showinfo("Card Selected", 
                           f"Selected card class {class_id}\n"
                           f"Click 'Save Label' to confirm or select a different card.")
        
    def setup_controls(self, parent):
        """Setup control buttons"""
        controls_frame = tk.Frame(parent, bg='#2b2b2b')
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        # Left side - navigation
        nav_frame = tk.Frame(controls_frame, bg='#2b2b2b')
        nav_frame.pack(side=tk.LEFT)
        
        self.prev_button = tk.Button(nav_frame, text="← Previous", 
                                    command=self.previous_card,
                                    state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.next_button = tk.Button(nav_frame, text="Next →", 
                                    command=self.next_card,
                                    state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        # Right side - actions
        action_frame = tk.Frame(controls_frame, bg='#2b2b2b')
        action_frame.pack(side=tk.RIGHT)
        
        self.skip_button = tk.Button(action_frame, text="Skip", 
                                    command=self.skip_card,
                                    state=tk.DISABLED)
        self.skip_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = tk.Button(action_frame, text="Save Label", 
                                    command=self.save_label,
                                    state=tk.DISABLED,
                                    bg='#4CAF50', fg='white')
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Load cards button
        load_button = tk.Button(action_frame, text="Load Cards...", 
                               command=self.load_cards_directory,
                               bg='#2196F3', fg='white')
        load_button.pack(side=tk.LEFT, padx=(10, 0))
        
    def load_cards_directory(self):
        """Load cards from directory"""
        from tkinter import filedialog
        
        directory = filedialog.askdirectory(
            title="Select directory with card images",
            initialdir="training_data/debug_cards"
        )
        
        if directory:
            self.load_cards_from_directory(directory)
    
    def load_cards_from_directory(self, directory):
        """Load all card images from directory"""
        directory = Path(directory)
        
        # Find all image files
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            image_files.extend(directory.glob(ext))
        
        # Filter out preview files
        image_files = [f for f in image_files if 'preview' not in f.name.lower() 
                      and 'comparison' not in f.name.lower()
                      and 'corner' not in f.name.lower()
                      and 'region' not in f.name.lower()]
        
        if not image_files:
            messagebox.showwarning("No Cards", f"No card images found in {directory}")
            return
        
        self.card_queue = sorted(image_files)
        self.current_index = 0
        
        # Enable controls
        self.update_navigation_buttons()
        self.skip_button.configure(state=tk.NORMAL)
        
        # Load first card
        self.load_current_card()
        
        messagebox.showinfo("Cards Loaded", f"Loaded {len(self.card_queue)} cards for labeling")
    
    def load_current_card(self):
        """Load the current card for labeling"""
        if not self.card_queue or self.current_index >= len(self.card_queue):
            return
        
        card_path = self.card_queue[self.current_index]
        self.current_card_path = card_path
        
        # Load and display card
        try:
            # Load image
            image = cv2.imread(str(card_path))
            if image is None:
                raise ValueError("Could not load image")
            
            # Extract corner region (what model sees)
            h, w = image.shape[:2]
            corner_h = int(h * 0.35)
            corner_w = int(w * 0.35)
            corner = image[:corner_h, :corner_w]
            
            # Convert to PIL and resize for display
            corner_rgb = cv2.cvtColor(corner, cv2.COLOR_BGR2RGB)
            corner_pil = Image.fromarray(corner_rgb)
            
            # Resize to fit display
            display_size = (300, 400)
            corner_pil = corner_pil.resize(display_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            self.current_card_image = ImageTk.PhotoImage(corner_pil)
            
            # Update display
            self.card_image_label.configure(image=self.current_card_image, text="")
            
            # Update info
            self.card_info_label.configure(text=f"File: {card_path.name}")
            self.progress_label.configure(text=f"Card {self.current_index + 1} of {len(self.card_queue)}")
            
            # Reset selection
            self.selected_class = None
            self.save_button.configure(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load card: {e}")
    
    def update_navigation_buttons(self):
        """Update navigation button states"""
        self.prev_button.configure(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_button.configure(state=tk.NORMAL if self.current_index < len(self.card_queue) - 1 else tk.DISABLED)
    
    def previous_card(self):
        """Go to previous card"""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_card()
            self.update_navigation_buttons()
    
    def next_card(self):
        """Go to next card"""
        if self.current_index < len(self.card_queue) - 1:
            self.current_index += 1
            self.load_current_card()
            self.update_navigation_buttons()
    
    def skip_card(self):
        """Skip current card"""
        self.next_card()
    
    def save_label(self):
        """Save the current label"""
        if self.selected_class is None:
            messagebox.showwarning("No Selection", "Please select a card first")
            return
        
        if self.current_card_path is None:
            messagebox.showwarning("No Card", "No card loaded")
            return
        
        try:
            # Save labeled card using existing function
            from label_single_card import save_labeled_card
            output_path = save_labeled_card(self.current_card_path, self.selected_class)
            
            messagebox.showinfo("Saved", f"Card labeled as class {self.selected_class}\n"
                                        f"Saved to: {output_path}")
            
            # Move to next card
            self.next_card()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save label: {e}")
    
    def run(self):
        """Start the GUI"""
        # Enable save button when card is selected
        def check_selection():
            if self.selected_class is not None:
                self.save_button.configure(state=tk.NORMAL)
            self.root.after(100, check_selection)
        
        check_selection()
        self.root.mainloop()


def main():
    """Main function"""
    print("=== GUI Card Labeler ===")
    print("Visual card labeling using Balatro tracker interface")
    print()
    
    try:
        app = CardLabelerGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()