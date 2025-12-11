#!/usr/bin/env python3
"""
Screen Capture - Captures frames from the game window
"""

from PIL import Image, ImageGrab
import numpy as np
from pathlib import Path


class ScreenCapture:
    """Handles screen capture for game monitoring"""
    
    def __init__(self):
        self.last_capture = None
    
    def capture_screen(self, region=None):
        """Capture the entire screen or a specific region
        
        Args:
            region: Optional tuple (x, y, width, height) to capture specific area
            
        Returns:
            PIL Image of the captured screen
        """
        if region:
            x, y, width, height = region
            bbox = (x, y, x + width, y + height)
            screenshot = ImageGrab.grab(bbox=bbox)
        else:
            screenshot = ImageGrab.grab()
        
        self.last_capture = screenshot
        return screenshot
    
    def capture_from_file(self, filepath):
        """Load an image from file for testing
        
        Args:
            filepath: Path to image file
            
        Returns:
            PIL Image
        """
        img = Image.open(filepath)
        self.last_capture = img
        return img
    
    def save_capture(self, filepath):
        """Save the last capture to file
        
        Args:
            filepath: Path to save the image
        """
        if self.last_capture:
            self.last_capture.save(filepath)
    
    def get_card_region(self, screenshot=None):
        """Extract the card hand region from a screenshot
        
        Balatro layout has 3 sections:
        - Left bar (Data): Left 25% of width, full height
        - Top right (Jokers): Right 75% of width, top 30% of height
        - Bottom right (Playing Cards): Right 75% of width, bottom 70% of height
        
        Args:
            screenshot: PIL Image, or None to use last_capture
            
        Returns:
            PIL Image of just the playing cards region (bottom right)
        """
        if screenshot is None:
            screenshot = self.last_capture
        
        if screenshot is None:
            return None
        
        width, height = screenshot.size
        
        # Playing cards region: right 75% of width, bottom 70% of height
        left_boundary = int(width * 0.25)  # Start at 25% (skip left bar)
        top_boundary = int(height * 0.30)  # Start at 30% down (skip jokers area)
        
        # Crop to playing cards region
        card_region = screenshot.crop((left_boundary, top_boundary, width, height))
        
        return card_region
    
    def get_joker_region(self, screenshot=None):
        """Extract the joker cards region from a screenshot
        
        Args:
            screenshot: PIL Image, or None to use last_capture
            
        Returns:
            PIL Image of just the joker region (top right)
        """
        if screenshot is None:
            screenshot = self.last_capture
        
        if screenshot is None:
            return None
        
        width, height = screenshot.size
        
        # Joker region: right 75% of width, top 30% of height
        left_boundary = int(width * 0.25)
        bottom_boundary = int(height * 0.30)
        
        joker_region = screenshot.crop((left_boundary, 0, width, bottom_boundary))
        
        return joker_region
    
    def get_data_region(self, screenshot=None):
        """Extract the data/UI region from a screenshot
        
        Args:
            screenshot: PIL Image, or None to use last_capture
            
        Returns:
            PIL Image of just the data region (left bar)
        """
        if screenshot is None:
            screenshot = self.last_capture
        
        if screenshot is None:
            return None
        
        width, height = screenshot.size
        
        # Data region: left 25% of width, full height
        right_boundary = int(width * 0.25)
        
        data_region = screenshot.crop((0, 0, right_boundary, height))
        
        return data_region
