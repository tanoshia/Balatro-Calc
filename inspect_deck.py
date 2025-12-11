#!/usr/bin/env python3
"""
Inspect the deck texture to understand the layout
"""

from PIL import Image
import cv2
import numpy as np

# Load 2x deck
deck = Image.open("resources/textures/2x/8BitDeck.png")
print(f"Deck size: {deck.size}")

card_w = deck.width // 13
card_h = deck.height // 4

print(f"Card size: {card_w}x{card_h}")

# Extract first few cards to see the layout
cards_to_show = [
    (0, 0, "2 of Hearts"),
    (1, 0, "3 of Hearts"),
    (12, 0, "Ace of Hearts"),
    (0, 3, "2 of Spades"),
]

for col, row, name in cards_to_show:
    left = col * card_w
    top = row * card_h
    card = deck.crop((left, top, left + card_w, top + card_h))
    
    # Convert to RGB with white background
    if card.mode == 'RGBA':
        white_bg = Image.new('RGB', card.size, (255, 255, 255))
        white_bg.paste(card, mask=card.split()[3])
        card = white_bg
    
    card_array = np.array(card)
    card_bgr = cv2.cvtColor(card_array, cv2.COLOR_RGB2BGR)
    
    # Show full card
    cv2.imshow(f'{name} - Full', card_bgr)
    
    # Show different corner sizes to find the best one
    for pct in [0.15, 0.20, 0.25, 0.30, 0.35]:
        h, w = card_array.shape[:2]
        corner_h = int(h * pct)
        corner_w = int(w * pct)
        
        # No border skip - start from top-left
        corner = card_array[:corner_h, :corner_w]
        corner_bgr = cv2.cvtColor(corner, cv2.COLOR_RGB2BGR)
        
        cv2.imshow(f'{name} - Corner {int(pct*100)}%', corner_bgr)

print("\nPress any key to close...")
cv2.waitKey(0)
cv2.destroyAllWindows()
