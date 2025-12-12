#!/usr/bin/env python3
"""
Compare detected cards with template database
Helps debug why cards aren't being recognized
"""

import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))

from src.utils import SpriteLoader


def compare_card_to_templates(card_image_path):
    """Compare a single card image to all templates"""
    
    # Try to load 2x resolution textures first
    sprites = []
    texture_2x_path = Path("resources/textures/2x/8BitDeck.png")
    
    if texture_2x_path.exists():
        print("Loading 2x resolution templates")
        deck_img = Image.open(texture_2x_path).convert('RGBA')
        
        # 8BitDeck is 13x4 grid
        card_width = deck_img.width // 13
        card_height = deck_img.height // 4
        
        for row in range(4):
            for col in range(13):
                left = col * card_width
                top = row * card_height
                card_sprite = deck_img.crop((left, top, left + card_width, top + card_height))
                
                # Convert RGBA to RGB with white background
                if card_sprite.mode == 'RGBA':
                    white_bg = Image.new('RGB', card_sprite.size, (255, 255, 255))
                    white_bg.paste(card_sprite, mask=card_sprite.split()[3])
                    card_sprite = white_bg
                
                sprites.append(card_sprite)
        
        print(f"Loaded {len(sprites)} card templates from 2x textures")
        print(f"2x template card size: {card_width}x{card_height}")
    else:
        print("Loading 1x resolution templates")
        sprite_loader = SpriteLoader()
        sheet_names = sprite_loader.get_sheet_names()
        if 'playing_cards' not in sheet_names:
            print("Error: playing_cards sheet not found")
            return
        sprites = sprite_loader.get_all_sprites('playing_cards', composite_back=True)
        print(f"Loaded {len(sprites)} card templates")
    
    # Load the card to recognize
    card_img = Image.open(card_image_path)
    card_array = np.array(card_img.convert('RGB'))
    
    print(f"Card image size: {card_img.size}")
    
    if sprites:
        first_sprite = sprites[0]
        print(f"Template size: {first_sprite.size}")
        
        # Show the full template for reference
        template_full = np.array(first_sprite.convert('RGB'))
        template_full_bgr = cv2.cvtColor(template_full, cv2.COLOR_RGB2BGR)
        cv2.imshow('Example Template (Full Card)', template_full_bgr)
    else:
        print("No templates loaded!")
        return
    
    # Extract top-left corner (35% x 35% from top-left)
    h, w = card_array.shape[:2]
    corner_h = int(h * 0.35)
    corner_w = int(w * 0.35)
    card_corner = card_array[:corner_h, :corner_w]
    
    # Show the full card
    card_full_bgr = cv2.cvtColor(card_array, cv2.COLOR_RGB2BGR)
    cv2.imshow('Full Card Being Analyzed', card_full_bgr)
    
    # Show the card corner
    card_corner_bgr = cv2.cvtColor(card_corner, cv2.COLOR_RGB2BGR)
    cv2.imshow('Card Corner (What we match)', card_corner_bgr)
    
    print(f"Card corner size: {card_corner.shape}")
    print(f"Card corner location: top-left, take {corner_h}x{corner_w}px (35% of card)")
    
    # Convert to grayscale
    card_corner_gray = cv2.cvtColor(card_corner, cv2.COLOR_RGB2GRAY)
    
    # Initialize ORB detector
    orb = cv2.ORB_create(nfeatures=500)
    
    # Detect keypoints and descriptors for card
    kp1, des1 = orb.detectAndCompute(card_corner_gray, None)
    
    print(f"Card corner keypoints: {len(kp1) if kp1 else 0}")
    
    if des1 is None or len(kp1) < 10:
        print("Not enough features in card, using template matching fallback")
        use_orb = False
    else:
        use_orb = True
        # Create BFMatcher
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    # Try matching against all templates
    results = []
    
    for idx, sprite in enumerate(sprites):
        template = np.array(sprite.convert('RGB'))
        
        # Extract template corner (35% from top-left)
        t_h, t_w = template.shape[:2]
        template_corner_h = int(t_h * 0.35)
        template_corner_w = int(t_w * 0.35)
        template_corner = template[:template_corner_h, :template_corner_w]
        template_corner_gray = cv2.cvtColor(template_corner, cv2.COLOR_RGB2GRAY)
        
        if use_orb:
            # ORB feature matching
            kp2, des2 = orb.detectAndCompute(template_corner_gray, None)
            
            if des2 is None or len(kp2) < 10:
                results.append((idx, 0, template_corner, 0, 0, 0))
                continue
            
            try:
                # Match descriptors
                matches = bf.match(des1, des2)
                matches = sorted(matches, key=lambda x: x.distance)
                
                # Take top 30% of matches
                good_matches = matches[:max(1, len(matches) // 3)]
                
                if len(good_matches) > 0:
                    avg_distance = sum(m.distance for m in good_matches) / len(good_matches)
                    # Score based on number of matches and quality
                    orb_score = len(good_matches) / (1 + avg_distance / 100)
                    # Normalize to 0-1 range
                    normalized_score = min(1.0, orb_score / 20)
                else:
                    normalized_score = 0
                
                results.append((idx, normalized_score, template_corner, len(good_matches), avg_distance, len(matches)))
            except:
                results.append((idx, 0, template_corner, 0, 0, 0))
        else:
            # Template matching fallback
            scale_h = corner_h / template_corner.shape[0]
            scale_w = corner_w / template_corner.shape[1]
            scale = (scale_h + scale_w) / 2
            
            scaled_h = min(int(template_corner.shape[0] * scale), corner_h)
            scaled_w = min(int(template_corner.shape[1] * scale), corner_w)
            
            template_resized = cv2.resize(template_corner, (scaled_w, scaled_h))
            
            result = cv2.matchTemplate(card_corner, template_resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            results.append((idx, max_val, template_resized, 0, 0, 0))
    
    # Sort by score
    results.sort(key=lambda x: x[1], reverse=True)
    
    # Show top 5 matches
    print("\nTop 5 matches:")
    if use_orb:
        print("Using ORB feature matching:")
        for i, (idx, score, template_corner, good_matches, avg_dist, total_matches) in enumerate(results[:5]):
            print(f"{i+1}. Card index {idx}: score={score:.3f} (good_matches={good_matches}, avg_dist={avg_dist:.1f}, total={total_matches})")
            
            # Show the template corner
            template_bgr = cv2.cvtColor(template_corner, cv2.COLOR_RGB2BGR)
            cv2.imshow(f'Match {i+1}: Card {idx} (score={score:.3f})', template_bgr)
    else:
        print("Using template matching:")
        for i, (idx, score, template_resized, _, _, _) in enumerate(results[:5]):
            print(f"{i+1}. Card index {idx}: score={score:.3f}")
            
            # Show the template corner
            template_bgr = cv2.cvtColor(template_resized, cv2.COLOR_RGB2BGR)
            cv2.imshow(f'Match {i+1}: Card {idx} (score={score:.3f})', template_bgr)
    
    print("\nPress any key to close...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compare_cards.py <card_image_path>")
        print("\nThis compares a single card image to all templates")
        print("Use debug_cards/card_X.png from test_vision.py output")
        sys.exit(1)
    
    card_path = sys.argv[1]
    
    if not Path(card_path).exists():
        print(f"Error: File not found: {card_path}")
        sys.exit(1)
    
    compare_card_to_templates(card_path)
