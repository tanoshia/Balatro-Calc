#!/usr/bin/env python3
"""
Modifier Classifier - CNN for detecting card modifiers (enhancements, editions, seals)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ModifierClassifier(nn.Module):
    """Multi-label classifier for card modifiers"""
    
    def __init__(self, num_enhancements=8, num_editions=4, num_seals=4):
        """
        Args:
            num_enhancements: Number of enhancement types
            num_editions: Number of edition types  
            num_seals: Number of seal types
        """
        super(ModifierClassifier, self).__init__()
        
        self.num_enhancements = num_enhancements
        self.num_editions = num_editions
        self.num_seals = num_seals
        
        # Shared convolutional backbone
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(0.3)
        
        # Adaptive pooling for variable input sizes
        self.adaptive_pool = nn.AdaptiveAvgPool2d((8, 8))
        
        # Separate heads for each modifier type
        feature_size = 128 * 8 * 8
        
        # Enhancement head (background modifiers like Bonus, Mult, Wild)
        self.enhancement_head = nn.Sequential(
            nn.Linear(feature_size, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_enhancements + 1)  # +1 for "no enhancement"
        )
        
        # Edition head (foil, holographic, polychrome, negative)
        self.edition_head = nn.Sequential(
            nn.Linear(feature_size, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_editions + 1)  # +1 for "no edition"
        )
        
        # Seal head (gold, red, blue, purple seals)
        self.seal_head = nn.Sequential(
            nn.Linear(feature_size, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_seals + 1)  # +1 for "no seal"
        )
        
    def forward(self, x):
        """Forward pass
        
        Args:
            x: Input tensor (batch_size, 3, height, width)
            
        Returns:
            dict: {'enhancement': logits, 'edition': logits, 'seal': logits}
        """
        # Shared feature extraction
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        
        # Adaptive pooling and flatten
        x = self.adaptive_pool(x)
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        
        # Separate predictions for each modifier type
        enhancement_logits = self.enhancement_head(x)
        edition_logits = self.edition_head(x)
        seal_logits = self.seal_head(x)
        
        return {
            'enhancement': enhancement_logits,
            'edition': edition_logits,
            'seal': seal_logits
        }
    
    def predict(self, x):
        """Get predictions with confidence scores
        
        Args:
            x: Input tensor
            
        Returns:
            dict: Predictions for each modifier type
        """
        self.eval()
        with torch.no_grad():
            outputs = self.forward(x)
            
            predictions = {}
            for modifier_type, logits in outputs.items():
                probabilities = F.softmax(logits, dim=1)
                predicted_class = torch.argmax(probabilities, dim=1)
                confidence = torch.max(probabilities, dim=1)[0]
                
                predictions[modifier_type] = {
                    'class': predicted_class,
                    'confidence': confidence,
                    'probabilities': probabilities
                }
            
        return predictions


class SimpleModifierDetector(nn.Module):
    """Simple binary classifier to detect if modifiers are present"""
    
    def __init__(self):
        super(SimpleModifierDetector, self).__init__()
        
        self.conv1 = nn.Conv2d(3, 16, kernel_size=5, padding=2)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=5, padding=2)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        
        self.pool = nn.MaxPool2d(2, 2)
        self.adaptive_pool = nn.AdaptiveAvgPool2d((4, 4))
        
        # Binary classification: has modifiers or not
        self.classifier = nn.Sequential(
            nn.Linear(64 * 4 * 4, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, 2)  # 0: no modifiers, 1: has modifiers
        )
        
    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        
        x = self.adaptive_pool(x)
        x = x.view(x.size(0), -1)
        
        return self.classifier(x)
    
    def predict(self, x):
        """Predict if card has modifiers"""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probabilities = F.softmax(logits, dim=1)
            has_modifiers = torch.argmax(probabilities, dim=1)
            confidence = torch.max(probabilities, dim=1)[0]
            
        return has_modifiers, confidence