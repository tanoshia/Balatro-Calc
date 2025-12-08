#!/usr/bin/env python3
"""
Modifier Manager - Handles card modifiers (enhancements, editions, seals, debuff)
"""

from PIL import Image, ImageTk, ImageChops
import tkinter as tk


class ModifierManager:
    """Manages card modifiers and their application"""
    
    def __init__(self, sprite_loader, card_order_config, modifiers_canvas, 
                 card_display_width, card_display_height, card_spacing, bg_color):
        self.sprite_loader = sprite_loader
        self.card_order_config = card_order_config
        self.modifiers_canvas = modifiers_canvas
        self.card_display_width = card_display_width
        self.card_display_height = card_display_height
        self.card_spacing = card_spacing
        self.bg_color = bg_color
        
        # Selected modifiers
        self.selected_enhancement = None
        self.selected_edition = None
        self.selected_seal = None
        self.selected_debuff = None
        
        # Callback for when modifiers change
        self.on_modifier_change = None
        
        # Modifier data
        self.modifier_data = []
        self.modifier_images = {}
        self.modifier_sprites = {}
        self.modifier_metadata = {}
        self.modifier_img_ids = {}
        self.modifier_positions = {}
        self.modifier_spacing_overrides = {}
        self.modifier_types = {}
        self.modifier_display_widths = {}
    
    def load_modifiers(self, filter_mode="All Modifiers"):
        """Load and display modifiers based on filter"""
        try:
            # Find the Card Backs sheet
            backs_sheet_name = self._find_backs_sheet()
            if not backs_sheet_name:
                print("Warning: Card Backs sheet not found for modifiers")
                return
            
            # Define non-scoring seal indices
            non_scoring_seals = [2, 32, 34]
            
            # Load modifier configuration
            modifiers = []
            if self.card_order_config and 'modifiers' in self.card_order_config:
                mod_config = self.card_order_config['modifiers']
                
                # Load enhancements
                modifiers.extend(self._load_modifier_category(
                    backs_sheet_name, mod_config, 'enhancements', 'enhancement'))
                
                # Load seals (with filtering)
                if 'seals' in mod_config:
                    indices = mod_config['seals']['indices']
                    render_modes = mod_config['seals'].get('render_modes', ['overlay'] * len(indices))
                    for i, idx in enumerate(indices):
                        if filter_mode == "Scoring Only" and idx in non_scoring_seals:
                            continue
                        sprite = self.sprite_loader.get_sprite(backs_sheet_name, idx, composite_back=False)
                        render_mode = render_modes[i] if i < len(render_modes) else 'overlay'
                        modifiers.append((idx, sprite, 'seal', render_mode))
                
                # Load editions
                editions_sheet_name = self._find_editions_sheet()
                if editions_sheet_name and 'editions' in mod_config:
                    indices = mod_config['editions']['indices']
                    render_modes = mod_config['editions'].get('render_modes', ['overlay'] * len(indices))
                    opacities = mod_config['editions'].get('opacity', [1.0] * len(indices))
                    blend_modes = mod_config['editions'].get('blend_modes', ['normal'] * len(indices))
                    for i, idx in enumerate(indices):
                        sprite = self.sprite_loader.get_sprite(editions_sheet_name, idx, composite_back=False)
                        render_mode = render_modes[i] if i < len(render_modes) else 'overlay'
                        opacity = opacities[i] if i < len(opacities) else 1.0
                        blend_mode = blend_modes[i] if i < len(blend_modes) else 'normal'
                        mod_type = 'debuff' if idx == 4 else 'edition'
                        modifiers.append((idx, sprite, mod_type, render_mode, opacity, blend_mode))
            
            self.modifier_data = modifiers
            
            # Set canvas size
            playing_cards_width = 13 * (self.card_display_width + self.card_spacing) - self.card_spacing
            self.modifiers_canvas.config(width=playing_cards_width, height=self.card_display_height)
            
            # Display modifiers
            for display_idx, modifier_data in enumerate(modifiers):
                self._create_modifier_button(display_idx, modifier_data)
            
        except Exception as e:
            print(f"Warning: Could not load modifiers: {e}")
    
    def _find_backs_sheet(self):
        """Find the card backs/enhancers sheet"""
        for name in self.sprite_loader.get_sheet_names():
            if name == 'enhancers' or ('back' in name.lower() and 
                ('enhancer' in name.lower() or 'seal' in name.lower())):
                return name
        return None
    
    def _find_editions_sheet(self):
        """Find the editions sheet"""
        for name in self.sprite_loader.get_sheet_names():
            if 'edition' in name.lower():
                return name
        return None
    
    def _load_modifier_category(self, sheet_name, mod_config, category_key, mod_type):
        """Load a category of modifiers"""
        modifiers = []
        if category_key in mod_config:
            indices = mod_config[category_key]['indices']
            render_modes = mod_config[category_key].get('render_modes', ['overlay'] * len(indices))
            for i, idx in enumerate(indices):
                sprite = self.sprite_loader.get_sprite(sheet_name, idx, composite_back=False)
                render_mode = render_modes[i] if i < len(render_modes) else 'overlay'
                modifiers.append((idx, sprite, mod_type, render_mode))
        return modifiers
    
    def _create_modifier_button(self, display_idx, modifier_data):
        """Create a clickable modifier button"""
        try:
            sprite_idx = modifier_data[0]
            sprite = modifier_data[1]
            mod_type = modifier_data[2]
            render_mode = modifier_data[3] if len(modifier_data) > 3 else 'overlay'
            opacity = modifier_data[4] if len(modifier_data) > 4 else 1.0
            blend_mode = modifier_data[5] if len(modifier_data) > 5 else 'normal'
            
            # Crop seals to circular area
            img = sprite.copy()
            if 'seal' in mod_type:
                original_width = img.width
                original_height = img.height
                left = int(original_width * (13 / 69))
                right = int(original_width * (40 / 69))
                img = img.crop((left, 0, right, original_height))
            
            img.thumbnail((self.card_display_width, self.card_display_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # Store references
            modifier_key = f"modifier_{mod_type}_{sprite_idx}"
            self.modifier_images[modifier_key] = photo
            self.modifier_sprites[modifier_key] = sprite
            self.modifier_metadata[modifier_key] = {
                'render_mode': render_mode,
                'opacity': opacity,
                'blend_mode': blend_mode
            }
            
            display_width = img.width if 'seal' in mod_type else self.card_display_width
            
            # Create image on canvas
            x = display_idx * (self.card_display_width + self.card_spacing)
            img_id = self.modifiers_canvas.create_image(x, 0, image=photo, anchor=tk.NW)
            
            # Store metadata
            self.modifier_img_ids[modifier_key] = img_id
            self.modifier_positions[modifier_key] = display_idx
            self.modifier_types[modifier_key] = mod_type
            self.modifier_display_widths[modifier_key] = display_width
            
            # Bind events
            self.modifiers_canvas.tag_bind(img_id, '<Button-1>',
                lambda e, key=modifier_key, idx=sprite_idx, mtype=mod_type:
                self.select_modifier(key, idx, mtype))
            self.modifiers_canvas.tag_bind(img_id, '<Enter>',
                lambda e: self.modifiers_canvas.config(cursor='hand2'))
            self.modifiers_canvas.tag_bind(img_id, '<Leave>',
                lambda e: self.modifiers_canvas.config(cursor=''))
            
        except Exception as e:
            print(f"Error creating modifier button: {e}")
    
    def select_modifier(self, modifier_key, sprite_idx, mod_type):
        """Select/deselect a modifier"""
        if 'enhancement' in mod_type:
            old = self.selected_enhancement
            self.selected_enhancement = (modifier_key, sprite_idx) if old != (modifier_key, sprite_idx) else None
        elif 'debuff' in mod_type:
            old = self.selected_debuff
            self.selected_debuff = (modifier_key, sprite_idx) if old != (modifier_key, sprite_idx) else None
        elif 'edition' in mod_type:
            old = self.selected_edition
            self.selected_edition = (modifier_key, sprite_idx) if old != (modifier_key, sprite_idx) else None
        elif 'seal' in mod_type:
            old = self.selected_seal
            self.selected_seal = (modifier_key, sprite_idx) if old != (modifier_key, sprite_idx) else None
        
        # Trigger callback to refresh card display
        if self.on_modifier_change:
            self.on_modifier_change()
        
        return True  # Signal that cards should be refreshed
    
    def apply_modifiers_to_card(self, base_sprite, card_face=None):
        """Apply selected modifiers to a card sprite"""
        # Check if we need card face for background modifiers
        use_card_face = False
        if self.selected_enhancement:
            modifier_key, _ = self.selected_enhancement
            metadata = self.modifier_metadata.get(modifier_key, {})
            if metadata.get('render_mode') == 'background':
                use_card_face = True
        
        # Start with appropriate base
        if use_card_face and card_face:
            result = card_face.copy().convert('RGBA')
            if self.selected_enhancement:
                modifier_key, _ = self.selected_enhancement
                enhancement = self.modifier_sprites[modifier_key].copy().convert('RGBA')
                if enhancement.size != result.size:
                    enhancement = enhancement.resize(result.size, Image.Resampling.LANCZOS)
                result = Image.alpha_composite(enhancement, result)
        else:
            result = base_sprite.copy().convert('RGBA')
            if self.selected_enhancement:
                modifier_key, _ = self.selected_enhancement
                metadata = self.modifier_metadata.get(modifier_key, {})
                if metadata.get('render_mode') != 'background':
                    enhancement = self.modifier_sprites[modifier_key].copy().convert('RGBA')
                    if enhancement.size != result.size:
                        enhancement = enhancement.resize(result.size, Image.Resampling.LANCZOS)
                    result = Image.alpha_composite(result, enhancement)
        
        # Apply edition
        result = self._apply_edition(result)
        
        # Apply seal
        if self.selected_seal:
            modifier_key, _ = self.selected_seal
            seal = self.modifier_sprites[modifier_key].copy().convert('RGBA')
            if seal.size != result.size:
                seal = seal.resize(result.size, Image.Resampling.LANCZOS)
            result = Image.alpha_composite(result, seal)
        
        # Apply debuff
        if self.selected_debuff:
            modifier_key, _ = self.selected_debuff
            debuff = self.modifier_sprites[modifier_key].copy().convert('RGBA')
            if debuff.size != result.size:
                debuff = debuff.resize(result.size, Image.Resampling.LANCZOS)
            result = Image.alpha_composite(result, debuff)
        
        return result
    
    def _apply_edition(self, result):
        """Apply edition modifier with blend modes"""
        if not self.selected_edition:
            return result
        
        modifier_key, _ = self.selected_edition
        edition = self.modifier_sprites[modifier_key].copy().convert('RGBA')
        if edition.size != result.size:
            edition = edition.resize(result.size, Image.Resampling.LANCZOS)
        
        metadata = self.modifier_metadata.get(modifier_key, {})
        opacity = metadata.get('opacity', 1.0)
        blend_mode = metadata.get('blend_mode', 'normal')
        
        if blend_mode == 'multiply':
            result_rgb = result.convert('RGB')
            edition_rgb = edition.convert('RGB')
            blended = ImageChops.multiply(result_rgb, edition_rgb)
            blended = blended.convert('RGBA')
            blended.putalpha(result.split()[3])
            return blended
        elif blend_mode == 'color':
            base_rgb = result.convert('RGB')
            edition_rgb = edition.convert('RGB')
            base_ycbcr = base_rgb.convert('YCbCr')
            edition_ycbcr = edition_rgb.convert('YCbCr')
            bY, bCb, bCr = base_ycbcr.split()
            _, eCb, eCr = edition_ycbcr.split()
            colored_ycbcr = Image.merge('YCbCr', (bY, eCb, eCr))
            colored_rgb = colored_ycbcr.convert('RGB')
            if opacity < 1.0:
                colored_rgb = Image.blend(base_rgb, colored_rgb, opacity)
            return Image.merge('RGBA', (*colored_rgb.split(), result.split()[3]))
        else:
            if opacity < 1.0:
                alpha = edition.split()[3]
                alpha = alpha.point(lambda p: int(p * opacity))
                edition.putalpha(alpha)
            return Image.alpha_composite(result, edition)
    
    def get_selected_modifiers(self):
        """Get list of currently selected modifiers"""
        modifiers_applied = []
        if self.selected_enhancement:
            _, idx = self.selected_enhancement
            modifiers_applied.append(('enhancement', idx))
        if self.selected_edition:
            _, idx = self.selected_edition
            modifiers_applied.append(('edition', idx))
        if self.selected_seal:
            _, idx = self.selected_seal
            modifiers_applied.append(('seal', idx))
        if self.selected_debuff:
            _, idx = self.selected_debuff
            modifiers_applied.append(('debuff', idx))
        return modifiers_applied
    
    def set_modifier_change_handler(self, handler):
        """Set callback for when modifiers change"""
        self.on_modifier_change = handler
    
    def clear_modifiers(self):
        """Clear all modifier data"""
        self.modifiers_canvas.delete('all')
        self.modifier_images.clear()
        self.modifier_img_ids.clear()
        self.modifier_positions.clear()
        self.modifier_types.clear()
        self.modifier_display_widths.clear()
