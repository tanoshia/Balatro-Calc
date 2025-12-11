#!/usr/bin/env python3
"""
Extract Cards from Screenshot - Extract individual cards from Balatro screenshots
"""

import sys
import cv2
import numpy as np
from pathlib import Path
from PIL import Image


def extract_playing_cards_region(screenshot_path):
    """Extract the playing cards region from a Balatro screenshot
    
    Balatro layout:
    - Data (Left 25%): Game stats, score, hands remaining  
    - Jokers (Top Right 75%, Top 30%): Joker cards and consumables
    - Playing Cards (Bottom Right 75%, Bottom 70%): Current hand of playing cards
    """
    # Load screenshot
    img = Image.open(screenshot_path)
    width, height = img.size
    
    print(f"Screenshot size: {width}x{height}")
    
    # Extract playing cards region (bottom right 75% x 70%)
    left = int(width * 0.25)   # Start at 25% from left (skip data section)
    top = int(height * 0.30)   # Start at 30% from top (skip jokers section)
    right = width              # Full width
    bottom = height            # Full height
    
    cards_region = img.crop((left, top, right, bottom))
    
    print(f"Cards region: {cards_region.size[0]}x{cards_region.size[1]}")
    print(f"Extracted from: ({left}, {top}) to ({right}, {bottom})")
    
    return cards_region


def detect_card_regions(image):
    """Detect individual card regions using edge detection"""
    # Convert PIL to OpenCV
    img_array = np.array(image)
    if len(img_array.shape) == 3:
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    else:
        img_cv = img_array
    
    # Convert to grayscale
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # Edge detection
    edges = cv2.Canny(gray, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by size and aspect ratio (cards are roughly 0.7 aspect ratio)
    card_regions = []
    min_area = 5000  # Minimum card area
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        aspect_ratio = w / h if h > 0 else 0
        
        # Cards should be roughly 0.6-0.8 aspect ratio and reasonably sized
        if area > min_area and 0.4 < aspect_ratio < 1.2:
            card_regions.append((x, y, w, h))
    
    # Sort by x position (left to right)
    card_regions.sort(key=lambda r: r[0])
    
    return card_regions


def extract_and_save_cards(screenshot_path, output_dir="training_data/debug_cards"):
    """Extract individual cards from screenshot and save them"""
    screenshot_path = Path(screenshot_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing: {screenshot_path}")
    
    # Extract playing cards region
    cards_region = extract_playing_cards_region(screenshot_path)
    
    # Save the cards region for reference
    region_path = output_dir / f"{screenshot_path.stem}_cards_region.png"
    cards_region.save(region_path)
    print(f"Saved cards region: {region_path}")
    
    # Detect individual cards
    card_regions = detect_card_regions(cards_region)
    print(f"Detected {len(card_regions)} potential cards")
    
    if not card_regions:
        print("No cards detected - you may need to adjust detection parameters")
        return
    
    # Extract and save each card
    saved_cards = []
    for i, (x, y, w, h) in enumerate(card_regions):
        # Extract card region
        card_img = cards_region.crop((x, y, x + w, y + h))
        
        # Save card
        card_path = output_dir / f"{screenshot_path.stem}_card{i+1}.png"
        card_img.save(card_path)
        saved_cards.append(card_path)
        
        print(f"  Card {i+1}: {w}x{h} -> {card_path}")
    
    print(f"\nExtracted {len(saved_cards)} cards to {output_dir}")
    print("Next steps:")
    print(f"1. Review the cards in {output_dir}")
    print(f"2. Run: python batch_label_cards.py {output_dir}")
    
    return saved_cards


def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_cards_from_screenshot.py <screenshot.png>")
        print("Example: python extract_cards_from_screenshot.py BalatroExample1.png")
        return
    
    screenshot_path = sys.argv[1]
    
    print("=== Card Extractor ===")
    print("This extracts individual cards from Balatro screenshots")
    print("using the correct screen layout (bottom right 75% x 70%)")
    print()
    
    extract_and_save_cards(screenshot_path)


if __name__ == "__main__":
    main()