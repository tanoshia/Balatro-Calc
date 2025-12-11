#!/usr/bin/env python3
"""
Card Classifier - CNN for recognizing playing cards and jokers
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models


class CardClassifier(nn.Module):
    """CNN for classifying Balatro cards (playing cards + jokers)"""
    
    def __init__(self, num_classes=52, use_pretrained=True):
        """
        Args:
            num_classes: Number of card types (52 playing cards, expand for jokers)
            use_pretrained: Use pretrained ResNet18 backbone
        """
        super(CardClassifier, self).__init__()
        
        self.num_classes = num_classes
        
        # Use ResNet18 as backbone (good balance of speed/accuracy)
        self.backbone = models.resnet18(pretrained=use_pretrained)
        
        # Replace final layer for our number of classes
        self.backbone.fc = nn.Linear(self.backbone.fc.in_features, num_classes)
        
        # Add dropout for regularization
        self.dropout = nn.Dropout(0.5)
        
    def forward(self, x):
        """Forward pass
        
        Args:
            x: Input tensor (batch_size, 3, height, width)
            
        Returns:
            Logits tensor (batch_size, num_classes)
        """
        # Extract features using ResNet backbone
        x = self.backbone.conv1(x)
        x = self.backbone.bn1(x)
        x = self.backbone.relu(x)
        x = self.backbone.maxpool(x)
        
        x = self.backbone.layer1(x)
        x = self.backbone.layer2(x)
        x = self.backbone.layer3(x)
        x = self.backbone.layer4(x)
        
        # Global average pooling
        x = self.backbone.avgpool(x)
        x = torch.flatten(x, 1)
        
        # Apply dropout
        x = self.dropout(x)
        
        # Final classification layer
        x = self.backbone.fc(x)
        
        return x
    
    def predict(self, x):
        """Get predictions with confidence scores
        
        Args:
            x: Input tensor
            
        Returns:
            tuple: (predicted_class, confidence_score)
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probabilities = F.softmax(logits, dim=1)
            predicted_class = torch.argmax(probabilities, dim=1)
            confidence = torch.max(probabilities, dim=1)[0]
            
        return predicted_class, confidence


class LightweightCardClassifier(nn.Module):
    """Lightweight CNN for faster inference"""
    
    def __init__(self, num_classes=52):
        super(LightweightCardClassifier, self).__init__()
        
        self.num_classes = num_classes
        
        # Lightweight convolutional layers
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout = nn.Dropout(0.5)
        
        # Adaptive pooling to handle variable input sizes
        self.adaptive_pool = nn.AdaptiveAvgPool2d((4, 4))
        
        # Fully connected layers
        self.fc1 = nn.Linear(256 * 4 * 4, 512)
        self.fc2 = nn.Linear(512, num_classes)
        
    def forward(self, x):
        # Convolutional layers with ReLU and pooling
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = self.pool(F.relu(self.conv4(x)))
        
        # Adaptive pooling to fixed size
        x = self.adaptive_pool(x)
        
        # Flatten for fully connected layers
        x = x.view(x.size(0), -1)
        
        # Fully connected layers
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        
        return x
    
    def predict(self, x):
        """Get predictions with confidence scores"""
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probabilities = F.softmax(logits, dim=1)
            predicted_class = torch.argmax(probabilities, dim=1)
            confidence = torch.max(probabilities, dim=1)[0]
            
        return predicted_class, confidence