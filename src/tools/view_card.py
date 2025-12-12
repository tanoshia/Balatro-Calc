#!/usr/bin/env python3
"""
Simple card viewer to see what we're working with
"""

import sys
from pathlib import Path
from PIL import Image
import cv2
import numpy as np

if len(sys.argv) < 2:
    print("Usage: python view_card.py <card_image>")
    sys.exit(1)

card_path = sys.argv[1]
img = Image.open(card_path)

print(f"Card size: {img.size}")

# Convert to numpy
img_array = np.array(img.convert('RGB'))
img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

# Show full card
cv2.imshow('Full Card', img_bgr)

# Extract and show corner (35% from top-left)
h, w = img_array.shape[:2]
corner_h = int(h * 0.35)
corner_w = int(w * 0.35)

corner = img_array[:corner_h, :corner_w]
corner_bgr = cv2.cvtColor(corner, cv2.COLOR_RGB2BGR)

cv2.imshow('Corner Region', corner_bgr)

# Also show what a 2x template looks like
template_path = Path("resources/textures/2x/8BitDeck.png")
if template_path.exists():
    deck = Image.open(template_path)
    card_w = deck.width // 13
    card_h = deck.height // 4
    
    # Show first card (2 of Hearts)
    first_card = deck.crop((0, 0, card_w, card_h))
    first_array = np.array(first_card.convert('RGB'))
    first_bgr = cv2.cvtColor(first_array, cv2.COLOR_RGB2BGR)
    cv2.imshow('Template Example (2H)', first_bgr)
    
    # Show its corner (35% from top-left)
    t_corner_h = int(card_h * 0.35)
    t_corner_w = int(card_w * 0.35)
    
    t_corner = first_array[:t_corner_h, :t_corner_w]
    t_corner_bgr = cv2.cvtColor(t_corner, cv2.COLOR_RGB2BGR)
    cv2.imshow('Template Corner', t_corner_bgr)

print("\nPress any key to close...")
cv2.waitKey(0)
cv2.destroyAllWindows()
