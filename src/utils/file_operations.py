#!/usr/bin/env python3
"""
File Operations - Utility functions for file handling and path operations
"""

import shutil
from pathlib import Path
import cv2


class FileOperations:
    """Utility class for file operations"""
    
    @staticmethod
    def ensure_directory(directory_path):
        """Ensure directory exists, create if it doesn't"""
        directory = Path(directory_path)
        directory.mkdir(parents=True, exist_ok=True)
        return directory
    
    @staticmethod
    def copy_file(source_path, destination_path):
        """Copy file from source to destination"""
        try:
            shutil.copy2(source_path, destination_path)
            return True, destination_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def save_image(image, output_path):
        """Save OpenCV image to file"""
        try:
            cv2.imwrite(str(output_path), image)
            return True, output_path
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def load_image(image_path):
        """Load image using OpenCV"""
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError("Could not load image")
            return True, image
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def find_image_files(directory, extensions=None):
        """Find all image files in a directory"""
        if extensions is None:
            extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        
        directory = Path(directory)
        if not directory.exists():
            return []
        
        image_files = []
        for ext in extensions:
            image_files.extend(directory.glob(f'*{ext}'))
            image_files.extend(directory.glob(f'*{ext.upper()}'))
        
        return sorted(image_files)
    
    @staticmethod
    def filter_processed_files(file_list, exclude_patterns=None):
        """Filter out processed/preview files"""
        if exclude_patterns is None:
            exclude_patterns = ['preview', 'comparison', 'region', 'processed']
        
        filtered_files = []
        for file_path in file_list:
            filename_lower = file_path.name.lower()
            if not any(pattern in filename_lower for pattern in exclude_patterns):
                filtered_files.append(file_path)
        
        return filtered_files
    
    @staticmethod
    def get_file_stem_without_suffix(file_path, suffixes_to_remove=None):
        """Get file stem without specific suffixes"""
        if suffixes_to_remove is None:
            suffixes_to_remove = ['_full', '_corner', '_processed']
        
        stem = Path(file_path).stem
        for suffix in suffixes_to_remove:
            stem = stem.replace(suffix, '')
        
        return stem
    
    @staticmethod
    def create_timestamped_filename(base_name, extension='.txt'):
        """Create a timestamped filename"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{base_name}_{timestamp}{extension}"