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
        
        # Initialize sprite loader
        self.sprite_loader = SpriteLoader()
        
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
            self._on_save
        )
        
        # Initialize managers
        self._setup_managers()
        
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
        """Handle card click - add to order with modifiers"""
        if card_name not in self.card_manager.base_card_sprites:
            return
        
        base_sprite = self.card_manager.base_card_sprites[card_name]
        card_face = self.card_manager.card_faces.get(card_name)
        
        # Apply modifiers
        final_sprite = self.modifier_manager.apply_modifiers_to_card(base_sprite, card_face)
        modifiers_applied = self.modifier_manager.get_selected_modifiers()
        
        # Add to order
        self.card_manager.add_card_to_order(card_name, final_sprite, modifiers_applied)
    
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
        """Clear card order"""
        self.card_manager.clear_order()
    
    def _on_undo(self):
        """Undo last card"""
        self.card_manager.undo_last()
    
    def _on_save(self):
        """Save card order"""
        success, message = self.card_manager.save_order()
        title = "Saved!" if success else "Error"
        messagebox.showinfo(title, message)
    
    def _on_window_resize(self, event):
        """Handle window resize"""
        if event.widget != self.root:
            return
        self._recalculate_positions()
    
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
