#!/usr/bin/env python3
"""
Trainer - Training loop for card and modifier classifiers
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
import numpy as np
from pathlib import Path
import json
from tqdm import tqdm
import matplotlib.pyplot as plt
import logging
from datetime import datetime


class Trainer:
    """Training manager for Balatro card classifiers"""
    
    def __init__(self, model, device=None, save_dir="models"):
        """
        Args:
            model: PyTorch model to train
            device: Device to train on (auto-detect if None)
            save_dir: Directory to save models
        """
        self.model = model
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        
        # Create logs directory
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging with timestamp
        timestamp = datetime.now().strftime("%m%d_%H%M")
        log_file = self.logs_dir / f"training_{timestamp}.log"
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Move model to device
        self.model.to(self.device)
        
        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': []
        }
        
        print(f"Training on device: {self.device}")
        print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
        print(f"Logging to: {log_file}")
        
        # Log initial info
        self.logger.info(f"=== Training Session Started ===")
        self.logger.info(f"Device: {self.device}")
        self.logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    def train_card_classifier(self, dataset, epochs=50, batch_size=32, 
                             learning_rate=0.001, val_split=0.2):
        """Train card classifier
        
        Args:
            dataset: BalatroCardDataset or similar
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            val_split: Validation split ratio
        """
        # Split dataset
        val_size = int(len(dataset) * val_split)
        train_size = len(dataset) - val_size
        train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
        
        # Create data loaders (num_workers=0 to avoid multiprocessing issues on macOS)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, 
                                 shuffle=True, num_workers=0)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, 
                               shuffle=False, num_workers=0)
        
        # Setup optimizer and loss
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate, weight_decay=1e-4)
        criterion = nn.CrossEntropyLoss()
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
        
        print(f"Training set: {len(train_dataset)} samples")
        print(f"Validation set: {len(val_dataset)} samples")
        
        best_val_acc = 0
        
        for epoch in range(epochs):
            # Training phase
            train_loss, train_acc = self._train_epoch(train_loader, optimizer, criterion)
            
            # Validation phase
            val_loss, val_acc = self._validate_epoch(val_loader, criterion)
            
            # Update learning rate
            scheduler.step(val_loss)
            
            # Save history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['train_acc'].append(train_acc)
            self.history['val_acc'].append(val_acc)
            
            # Log progress to file
            self.logger.info(f"Epoch {epoch+1}/{epochs}")
            self.logger.info(f"  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}")
            self.logger.info(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
            self.logger.info(f"  LR: {optimizer.param_groups[0]['lr']:.6f}")
            
            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                self.save_model(f"card_classifier_best.pth", epoch, val_acc)
                self.logger.info(f"  New best model saved! Val Acc: {val_acc:.4f}")
            
            self.logger.info("-" * 50)
        
        # Save final model
        self.save_model(f"card_classifier_final.pth", epochs, val_acc)
        
        # Log final results
        self.logger.info(f"=== Training Completed ===")
        self.logger.info(f"Best validation accuracy: {best_val_acc:.4f}")
        self.logger.info(f"Final validation accuracy: {val_acc:.4f}")
        
        # Plot training curves
        self.plot_training_curves()
        
        return self.history
    
    def _train_epoch(self, train_loader, optimizer, criterion):
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        pbar = tqdm(train_loader, desc="Training")
        for batch in pbar:
            images = batch['image'].to(self.device)
            labels = batch['card_class'].to(self.device)
            
            # Forward pass
            optimizer.zero_grad()
            outputs = self.model(images)
            loss = criterion(outputs, labels)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            # Statistics
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            # Update progress bar
            pbar.set_postfix({
                'Loss': f'{loss.item():.4f}',
                'Acc': f'{100 * correct / total:.2f}%'
            })
        
        return total_loss / len(train_loader), correct / total
    
    def _validate_epoch(self, val_loader, criterion):
        """Validate for one epoch"""
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validation"):
                images = batch['image'].to(self.device)
                labels = batch['card_class'].to(self.device)
                
                outputs = self.model(images)
                loss = criterion(outputs, labels)
                
                total_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        return total_loss / len(val_loader), correct / total
    
    def save_model(self, filename, epoch, accuracy):
        """Save model checkpoint"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'accuracy': accuracy,
            'history': self.history
        }
        
        save_path = self.save_dir / filename
        torch.save(checkpoint, save_path)
        print(f"Model saved to {save_path}")
    
    def load_model(self, filename):
        """Load model checkpoint"""
        load_path = self.save_dir / filename
        checkpoint = torch.load(load_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.history = checkpoint.get('history', {})
        
        print(f"Model loaded from {load_path}")
        print(f"Epoch: {checkpoint['epoch']}, Accuracy: {checkpoint['accuracy']:.4f}")
        
        return checkpoint
    
    def plot_training_curves(self):
        """Plot training and validation curves"""
        if not self.history['train_loss']:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Loss curves
        ax1.plot(self.history['train_loss'], label='Train Loss')
        ax1.plot(self.history['val_loss'], label='Val Loss')
        ax1.set_title('Training and Validation Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        ax1.grid(True)
        
        # Accuracy curves
        ax2.plot(self.history['train_acc'], label='Train Acc')
        ax2.plot(self.history['val_acc'], label='Val Acc')
        ax2.set_title('Training and Validation Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(self.save_dir / 'training_curves.png', dpi=150, bbox_inches='tight')
        plt.show()
        
        print(f"Training curves saved to {self.save_dir / 'training_curves.png'}")


class ModifierTrainer(Trainer):
    """Specialized trainer for multi-label modifier classification"""
    
    def train_modifier_classifier(self, dataset, epochs=30, batch_size=32, learning_rate=0.001):
        """Train modifier classifier with multi-label loss"""
        # TODO: Implement multi-label training for modifiers
        # This would use BCEWithLogitsLoss for each modifier type
        pass