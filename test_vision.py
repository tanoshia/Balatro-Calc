#!/usr/bin/env python3
"""
Test script for card recognition - helps debug and tune parameters
"""

import sys
from pathlib import Path
from PIL import Image
import cv2
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils import SpriteLoader
from src.vision import CardRecognizer, ScreenCapture


def visualize_detection(image_path):
    """Visualize card detection process"""
    print(f"Loading image: {image_path}")
    
    # Load image
    img = Image.open(image_path)
    print(f"Image size: {img.size}")
    width, height = img.size
    
    # Convert to OpenCV format
    img_array = np.array(img.convert('RGB'))
    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Draw region boundaries on original
    annotated = img_bgr.copy()
    left_boundary = int(width * 0.25)
    top_boundary = int(height * 0.30)
    
    # Draw lines to show regions
    cv2.line(annotated, (left_boundary, 0), (left_boundary, height), (0, 255, 0), 3)  # Vertical line
    cv2.line(annotated, (left_boundary, top_boundary), (width, top_boundary), (0, 255, 0), 3)  # Horizontal line
    
    # Add labels
    cv2.putText(annotated, "Data (Left 25%)", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(annotated, "Jokers (Top 30%)", (left_boundary + 10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(annotated, "Playing Cards (Bottom 70%)", (left_boundary + 10, top_boundary + 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    cv2.imshow('Original with Regions', annotated)
    
    # Extract card region using proper boundaries
    card_region = img_array[top_boundary:, left_boundary:]
    card_region_bgr = cv2.cvtColor(card_region, cv2.COLOR_RGB2BGR)
    
    print(f"Card region size: {card_region.shape}")
    cv2.imshow('Card Region (Playing Cards)', card_region_bgr)
    
    # Convert to grayscale
    gray = cv2.cvtColor(card_region, cv2.COLOR_RGB2GRAY)
    cv2.imshow('Grayscale', gray)
    
    # Edge detection
    edges = cv2.Canny(gray, 50, 150)
    cv2.imshow('Edges', edges)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"Found {len(contours)} contours")
    
    # Draw all contours
    contour_img = card_region_bgr.copy()
    cv2.drawContours(contour_img, contours, -1, (0, 255, 0), 2)
    cv2.imshow('All Contours', contour_img)
    
    # Filter contours by size and aspect ratio
    card_regions = []
    filtered_img = card_region_bgr.copy()
    
    for i, contour in enumerate(contours):
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / h if h > 0 else 0
        area = w * h
        
        print(f"Contour {i}: x={x}, y={y}, w={w}, h={h}, aspect={aspect_ratio:.2f}, area={area}")
        
        # Draw all rectangles in red
        cv2.rectangle(filtered_img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        
        # Check if it matches card criteria
        if 0.5 < aspect_ratio < 0.9 and area > 1000:
            card_regions.append((x, y, w, h))
            # Draw matching cards in green
            cv2.rectangle(filtered_img, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.putText(filtered_img, f"Card {len(card_regions)}", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    print(f"\nFiltered to {len(card_regions)} potential cards")
    cv2.imshow('Filtered Contours', filtered_img)
    
    print("\nPress any key to close windows...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return card_regions


def test_recognition(image_path):
    """Test full recognition pipeline"""
    print("\n=== Testing Full Recognition Pipeline ===\n")
    
    # Initialize
    sprite_loader = SpriteLoader()
    screen_capture = ScreenCapture()
    card_recognizer = CardRecognizer(sprite_loader)
    
    # Load image
    screenshot = screen_capture.capture_from_file(image_path)
    
    # Extract card region
    card_region = screen_capture.get_card_region(screenshot)
    
    if card_region:
        print(f"Card region extracted: {card_region.size}")
        
        # Detect card regions first
        card_regions = card_recognizer.detect_cards(card_region)
        print(f"Detected {len(card_regions)} card regions")
        
        # Save each detected card for inspection
        debug_dir = Path("debug_cards")
        debug_dir.mkdir(exist_ok=True)
        
        for i, (x, y, w, h) in enumerate(card_regions):
            card_img = card_region.crop((x, y, x + w, y + h))
            card_img.save(debug_dir / f"card_{i+1}.png")
            print(f"  Saved card {i+1} to debug_cards/card_{i+1}.png (size: {w}x{h})")
        
        # Recognize cards
        recognized_cards = card_recognizer.recognize_hand(card_region)
        
        print(f"\nRecognized {len(recognized_cards)} cards:")
        for i, card in enumerate(recognized_cards):
            if card['index'] is not None:
                print(f"  Card {i+1}: index={card['index']}, confidence={card['confidence']:.2f}")
            else:
                print(f"  Card {i+1}: NOT RECOGNIZED (confidence={card['confidence']:.2f})")
        
        # Show template info
        print(f"\nTemplate database has {len(card_recognizer.card_templates)} cards")
        if card_recognizer.card_templates:
            first_template = list(card_recognizer.card_templates.values())[0]
            print(f"Template size: {first_template.shape}")
    else:
        print("Failed to extract card region")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_vision.py <image_path>")
        print("\nThis script helps debug card detection by showing:")
        print("  - Original image")
        print("  - Extracted card region")
        print("  - Edge detection")
        print("  - Detected contours")
        print("  - Filtered card regions")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)
    
    # Visualize detection
    card_regions = visualize_detection(image_path)
    
    # Test full pipeline
    test_recognition(image_path)
