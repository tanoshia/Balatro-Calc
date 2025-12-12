#!/usr/bin/env python3
"""
Card Display Manager - Handles card display with modifiers for matched card preview
"""

import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path


class CardDisplayManager:
    """Manages card display with full modifier support"""
    
    def __init__(self, ui, card_manager, modifier_manager, card_order_config):
        self.ui = ui
        self.card_manager = card_manager
        self.modifier_manager = modifier_manager
        self.card_order_config = card_order_config
        
        # Display state
        self.matched_card_info = None
        self.matched_card_sprite = None
    
    def update_matched_card_display(self, card_class, status="selected"):
        """Update the matched card display to show selected/confirmed card with modifiers"""
        try:
            from PIL import ImageTk, Image
            
            if card_class == "not_card":
                # Show "Not a Card" indicator
                self.ui.matched_card_canvas.delete("all")
                self.ui.matched_card_canvas.create_text(75, 100, text="NOT A CARD", 
                                                       fill='#f44336', font=('Arial', 10, 'bold'))
                self.ui.match_status.configure(text=f"Status: {status.title()}")
                
            elif str(card_class).startswith("suit_only"):
                # Show suit symbol for suit-only selections
                suit_part = str(card_class).replace("suit_only_", "")
                suit_names = {"s": "♠", "h": "♥", "c": "♣", "d": "♦"}
                suit_symbol = suit_names.get(suit_part, "?")
                
                self.ui.matched_card_canvas.delete("all")
                self.ui.matched_card_canvas.create_text(75, 80, text="SUIT ONLY", 
                                                       fill='#ff9800', font=('Arial', 10, 'bold'))
                self.ui.matched_card_canvas.create_text(75, 120, text=suit_symbol, 
                                                       fill='#ff9800', font=('Arial', 24, 'bold'))
                self.ui.match_status.configure(text=f"Status: {status.title()}")
                
            elif isinstance(card_class, int) and 0 <= card_class <= 51:
                # Use card manager system for actual cards with full modifier support
                self._display_card_with_modifiers(card_class, status)
                
            else:
                # Unknown selection
                self.ui.matched_card_canvas.delete("all")
                self.ui.matched_card_canvas.create_text(75, 100, text="Unknown", 
                                                       fill='#cccccc', font=('Arial', 9))
                self.ui.match_status.configure(text=f"Status: {status.title()}")
                
        except Exception as e:
            print(f"Error updating matched card display: {e}")
            self.ui.matched_card_canvas.delete("all")
            self.ui.matched_card_canvas.create_text(75, 100, text="Error", 
                                                   fill='#f44336', font=('Arial', 9))
    
    def _display_card_with_modifiers(self, card_class, status):
        """Display a card with all currently selected modifiers applied"""
        try:
            # Get card order mapping
            card_order = self.card_order_config['playing_cards_order']['sprite_sheet_mapping']['order']
            
            # Find card name by sprite index
            card_name = None
            sprite_idx = None
            for name, idx in zip(self.card_manager.base_card_sprites.keys(), card_order):
                if idx == card_class:
                    card_name = name
                    sprite_idx = idx
                    break
            
            if card_name and card_name in self.card_manager.base_card_sprites:
                # Get base sprite and face
                base_sprite = self.card_manager.base_card_sprites[card_name]
                card_face = self.card_manager.card_faces.get(card_name)
                
                # Apply modifiers using existing system
                final_sprite = self.modifier_manager.apply_modifiers_to_card(base_sprite, card_face)
                
                # Resize for matched card display
                display_width = 100
                display_height = 133
                final_sprite = final_sprite.resize((display_width, display_height), Image.Resampling.LANCZOS)
                
                # Convert and display
                card_photo = ImageTk.PhotoImage(final_sprite)
                self.ui.matched_card_canvas.delete("all")
                self.ui.matched_card_canvas.create_image(75, 100, image=card_photo, anchor=tk.CENTER)
                self.ui.matched_card_canvas.image = card_photo
                
                # Store info for persistence
                self.matched_card_info = {
                    'card_class': card_class,
                    'status': status,
                    'sprite_idx': sprite_idx
                }
                self.matched_card_sprite = card_photo
                
                # Update status with card name
                suits = ["Hearts", "Clubs", "Diamonds", "Spades"]
                ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
                suit_idx = card_class // 13
                rank_idx = card_class % 13
                
                if suit_idx < len(suits) and rank_idx < len(ranks):
                    card_name = f"{ranks[rank_idx]} of {suits[suit_idx]}"
                    self.ui.match_status.configure(text=f"{card_name}\nStatus: {status.title()}")
                else:
                    self.ui.match_status.configure(text=f"Class {card_class}\nStatus: {status.title()}")
            else:
                # Fallback for unknown card
                self.ui.matched_card_canvas.delete("all")
                self.ui.matched_card_canvas.create_text(75, 100, text=f"Card {card_class}", 
                                                       fill='#cccccc', font=('Arial', 9))
                self.ui.match_status.configure(text=f"Class {card_class}\nStatus: {status.title()}")
                
        except Exception as e:
            print(f"Error displaying card with modifiers: {e}")
            # Fallback display
            self.ui.matched_card_canvas.delete("all")
            self.ui.matched_card_canvas.create_text(75, 100, text=f"Card {card_class}", 
                                                   fill='#cccccc', font=('Arial', 9))
            self.ui.match_status.configure(text=f"Status: {status.title()}")
    
    def clear_matched_card_display(self):
        """Clear the matched card display"""
        self.ui.matched_card_canvas.delete("all")
        self.ui.matched_card_canvas.create_text(75, 100, text="No selection", 
                                               fill='#cccccc', font=('Arial', 9))
        self.ui.match_status.configure(text="")
        self.matched_card_info = None
        self.matched_card_sprite = None
    
    def restore_matched_card_display(self):
        """Restore matched card display after window operations"""
        if self.matched_card_info and self.matched_card_sprite:
            try:
                # Restore the image
                self.ui.matched_card_canvas.delete("all")
                self.ui.matched_card_canvas.create_image(75, 100, image=self.matched_card_sprite, anchor=tk.CENTER)
                self.ui.matched_card_canvas.image = self.matched_card_sprite
                
                # Restore status
                card_class = self.matched_card_info['card_class']
                status = self.matched_card_info['status']
                
                suits = ["Hearts", "Clubs", "Diamonds", "Spades"]
                ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
                suit_idx = card_class // 13
                rank_idx = card_class % 13
                
                if suit_idx < len(suits) and rank_idx < len(ranks):
                    card_name = f"{ranks[rank_idx]} of {suits[suit_idx]}"
                    self.ui.match_status.configure(text=f"{card_name}\nStatus: {status.title()}")
                else:
                    self.ui.match_status.configure(text=f"Class {card_class}\nStatus: {status.title()}")
                    
            except Exception as e:
                print(f"Error restoring matched card display: {e}")
    
    def display_category_in_matched_display(self, category_name):
        """Show category label in the matched card display"""
        try:
            self.ui.matched_card_canvas.delete("all")
            
            # Show category name with appropriate styling
            colors = {
                "Not a Card": '#f44336',      # Red
                "Card Backs": '#2196f3',      # Blue
                "Booster Packs": '#ff9800',   # Orange
                "Consumables": '#9c27b0',     # Purple
                "Jokers": '#4caf50'           # Green
            }
            color = colors.get(category_name, '#cccccc')
            
            self.ui.matched_card_canvas.create_text(75, 100, text=category_name.upper(), 
                                                   fill=color, font=('Arial', 10, 'bold'))
            self.ui.match_status.configure(text=f"Status: Confirmed")
            
        except Exception as e:
            print(f"Error showing category in matched display: {e}")
    
    def display_suit_in_matched_display(self, suit_name, status="Already Labeled"):
        """Display suit symbol in matched card display"""
        try:
            from PIL import Image, ImageTk
            self.ui.matched_card_canvas.delete("all")
            
            self.ui.matched_card_canvas.create_text(75, 60, text="SUIT ONLY", 
                                                   fill='#ff9800', font=('Arial', 10, 'bold'))
            
            # Use actual suit sprite if available
            if hasattr(self.ui, 'suit_sprites') and suit_name in self.ui.suit_sprites:
                suit_sprite = self.ui.suit_sprites[suit_name]
                # Resize suit for matched display (smaller than full card)
                display_suit = suit_sprite.resize((60, 80), Image.Resampling.LANCZOS)
                suit_photo = ImageTk.PhotoImage(display_suit)
                
                self.ui.matched_card_canvas.create_image(75, 130, image=suit_photo, anchor=tk.CENTER)
                self.ui.matched_card_canvas.image = suit_photo  # Keep reference
            else:
                # Fallback to text symbol if sprites not available
                suit_symbols = {"Hearts": "♥", "Clubs": "♣", "Diamonds": "♦", "Spades": "♠"}
                suit_symbol = suit_symbols.get(suit_name, "?")
                self.ui.matched_card_canvas.create_text(75, 130, text=suit_symbol, 
                                                       fill='#ff9800', font=('Arial', 24, 'bold'))
            
            self.ui.match_status.configure(text=f"Suit Only ({suit_name})\nStatus: {status}")
            
        except Exception as e:
            print(f"Error displaying suit in matched display: {e}")