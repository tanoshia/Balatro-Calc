#!/usr/bin/env python3
"""
Sprite Sheet Loader
Dynamically loads and splits sprite sheets based on filename convention
Filename format: "COLSxROWS Description.png" (e.g., "13x4 Playing Cards.png")
"""

import re
import json
from PIL import Image
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class SpriteLoader:
    def __init__(self, assets_dir: str = "assets", resource_mapping: str = "resource_mapping.json"):
        """Initialize sprite loader with assets directory and resource mapping"""
        self.assets_dir = Path(assets_dir)
        self.resource_mapping_path = Path(resource_mapping)
        self.sprite_cache = {}
        self.sheets = {}
        self.card_back = None
        self._load_resource_mapping()
        self._scan_sheets()
        self._load_card_back()
    
    def _load_resource_mapping(self):
        """Load resource mapping configuration"""
        self.resource_mapping = {}
        if self.resource_mapping_path.exists():
            try:
                with open(self.resource_mapping_path, 'r') as f:
                    self.resource_mapping = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load resource mapping: {e}")
    
    def _scan_sheets(self):
        """Scan for sprite sheets using resource mapping first, then fallback to assets"""
        # Try resource mapping first
        if self.resource_mapping and 'sprite_sheets' in self.resource_mapping:
            resource_path = Path(self.resource_mapping.get('resource_path', 'resources/textures/1x/'))
            
            for sheet_name, sheet_info in self.resource_mapping['sprite_sheets'].items():
                resource_file = sheet_info.get('resource_file')
                fallback_file = sheet_info.get('fallback_file')
                grid = sheet_info.get('grid', {})
                
                # Try resource file first
                file_path = None
                if resource_file and resource_path.exists():
                    resource_full_path = resource_path / resource_file
                    if resource_full_path.exists():
                        file_path = resource_full_path
                
                # Fallback to assets
                if not file_path and fallback_file:
                    fallback_full_path = self.assets_dir / fallback_file
                    if fallback_full_path.exists():
                        file_path = fallback_full_path
                
                # Add to sheets if found
                if file_path and grid.get('cols') and grid.get('rows'):
                    self.sheets[sheet_name] = {
                        'file': file_path,
                        'cols': grid['cols'],
                        'rows': grid['rows'],
                        'name': sheet_name
                    }
        
        # Also scan assets directory for filename-based sheets (backward compatibility)
        if self.assets_dir.exists():
            for file in self.assets_dir.glob("*.png"):
                grid_info = self._parse_filename(file.name)
                if grid_info:
                    cols, rows, name = grid_info
                    # Only add if not already defined in resource mapping
                    if name not in self.sheets:
                        self.sheets[name] = {
                            'file': file,
                            'cols': cols,
                            'rows': rows,
                            'name': name
                        }
    
    def _load_card_back(self):
        """Load the default card back texture from the backs sprite sheet"""
        # Look for the card backs sheet (check resource mapping names first)
        backs_sheet = None
        for name, sheet in self.sheets.items():
            # Check for resource mapping names or filename-based names
            if name == 'enhancers' or ('back' in name.lower() and ('card' in name.lower() or 'enhancer' in name.lower() or 'seal' in name.lower())):
                backs_sheet = sheet
                break
        
        if backs_sheet:
            try:
                # Extract row 1, col 2 (index 1)
                # In a grid: row 0 (first row), col 1 (second column) = index 1
                index = 1  # Second card in first row
                self.card_back = self._extract_sprite(backs_sheet, index)
                print(f"Loaded card back from '{backs_sheet['name']}' (index {index})")
            except Exception as e:
                print(f"Warning: Could not load card back: {e}")
                self.card_back = None
        else:
            print("Warning: No card backs sprite sheet found")
    
    def _parse_filename(self, filename: str) -> Optional[Tuple[int, int, str]]:
        """Parse filename to extract grid dimensions
        Format: "COLSxROWS Description.png"
        Example: "13x4 Playing Cards.png" -> (13, 4, "Playing Cards")
        """
        match = re.match(r'^(\d+)x(\d+)\s+(.+)\.png$', filename, re.IGNORECASE)
        if match:
            cols = int(match.group(1))
            rows = int(match.group(2))
            name = match.group(3)
            return (cols, rows, name)
        return None
    
    def get_sprite(self, sheet_name: str, index: int, composite_back: bool = False) -> Image.Image:
        """Get a specific sprite from a sheet by index
        
        Args:
            sheet_name: Name of the sprite sheet
            index: Index of the sprite in the sheet
            composite_back: If True, composite the sprite onto the card back
        """
        cache_key = f"{sheet_name}:{index}:{composite_back}"
        
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]
        
        sheet = self.sheets.get(sheet_name)
        if not sheet:
            raise ValueError(f"Sheet '{sheet_name}' not found")
        
        sprite = self._extract_sprite(sheet, index)
        
        # Composite onto card back if requested and available
        if composite_back and self.card_back:
            sprite = self._composite_on_back(sprite)
        
        self.sprite_cache[cache_key] = sprite
        
        return sprite
    
    def get_all_sprites(self, sheet_name: str, composite_back: bool = False) -> List[Image.Image]:
        """Get all sprites from a sheet as a list
        
        Args:
            sheet_name: Name of the sprite sheet
            composite_back: If True, composite sprites onto the card back
        """
        sheet = self.sheets.get(sheet_name)
        if not sheet:
            raise ValueError(f"Sheet '{sheet_name}' not found")
        
        total_cards = sheet['cols'] * sheet['rows']
        sprites = []
        
        for idx in range(total_cards):
            cache_key = f"{sheet_name}:{idx}:{composite_back}"
            if cache_key not in self.sprite_cache:
                sprite = self._extract_sprite(sheet, idx)
                if composite_back and self.card_back:
                    sprite = self._composite_on_back(sprite)
                self.sprite_cache[cache_key] = sprite
            sprites.append(self.sprite_cache[cache_key])
        
        return sprites
    
    def _extract_sprite(self, sheet: dict, index: int) -> Image.Image:
        """Extract a single sprite from the sheet"""
        file_path = sheet['file']
        if not file_path.exists():
            raise FileNotFoundError(f"Sprite sheet not found: {file_path}")
        
        # Load image and calculate card dimensions
        img = Image.open(file_path).convert('RGBA')  # Ensure RGBA for transparency
        img_width, img_height = img.size
        
        cols = sheet['cols']
        rows = sheet['rows']
        card_width = img_width // cols
        card_height = img_height // rows
        
        # Calculate position in grid
        row = index // cols
        col = index % cols
        
        # Calculate pixel coordinates
        x = col * card_width
        y = row * card_height
        
        # Crop and return
        sprite = img.crop((x, y, x + card_width, y + card_height))
        
        return sprite
    
    def _composite_on_back(self, card_face: Image.Image) -> Image.Image:
        """Composite a card face onto the card back texture"""
        if not self.card_back:
            return card_face
        
        # Ensure both images are RGBA
        back = self.card_back.convert('RGBA')
        face = card_face.convert('RGBA')
        
        # Resize back to match face if needed
        if back.size != face.size:
            back = back.resize(face.size, Image.Resampling.LANCZOS)
        
        # Composite: paste face onto back using face's alpha channel
        result = back.copy()
        result.paste(face, (0, 0), face)
        
        return result
    
    def get_sheet_names(self) -> List[str]:
        """Get list of available sheet names"""
        return list(self.sheets.keys())
    
    def get_sheet_info(self, sheet_name: str) -> dict:
        """Get information about a specific sheet"""
        return self.sheets.get(sheet_name)


def main():
    """Example usage and testing"""
    loader = SpriteLoader()
    
    sheet_names = loader.get_sheet_names()
    print(f"Found {len(sheet_names)} sprite sheet(s):")
    
    for name in sheet_names:
        info = loader.get_sheet_info(name)
        total = info['cols'] * info['rows']
        print(f"  - {name}: {info['cols']}x{info['rows']} ({total} cards)")
    
    if not sheet_names:
        print("\nNo sprite sheets found in assets/ directory")
        print("Filename format: 'COLSxROWS Description.png'")
        print("Example: '13x4 Playing Cards.png'")
        return
    
    # Prioritize playing cards for extraction
    sheet_name = None
    for name in sheet_names:
        if 'high contrast' in name.lower() and 'playing' in name.lower():
            sheet_name = name
            break
    
    if not sheet_name:
        for name in sheet_names:
            if 'playing' in name.lower():
                sheet_name = name
                break
    
    if not sheet_name:
        sheet_name = sheet_names[0]
    
    print(f"\nExtracting cards from '{sheet_name}'...")
    
    sprites = loader.get_all_sprites(sheet_name)
    print(f"Loaded {len(sprites)} cards")
    
    # Save individual cards to verify
    output_dir = Path("cards")
    output_dir.mkdir(exist_ok=True)
    
    for idx, sprite in enumerate(sprites):
        output_path = output_dir / f"{sheet_name}_{idx:02d}.png"
        sprite.save(output_path)
        print(f"Saved: {output_path}")
    
    print(f"\nAll cards saved to '{output_dir}' directory")


if __name__ == "__main__":
    main()
