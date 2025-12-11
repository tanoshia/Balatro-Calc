#!/usr/bin/env python3
"""
Train Card Classifier - Main training script for card recognition
"""

import sys
from pathlib import Path
import torch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ml.card_classifier import CardClassifier, LightweightCardClassifier
from src.ml.data_generator import BalatroCardDataset, RealDatasetFromScreenshots
from src.ml.trainer import Trainer


def main():
    """Main training function"""
    print("=== Balatro Card Classifier Training ===\n")
    
    # Check GPU availability
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print(f"Using device: {device}")
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
    elif torch.backends.mps.is_available():
        device = torch.device('mps')
        print(f"Using device: {device}")
        print("GPU: Apple Silicon (Metal Performance Shaders)")
    else:
        device = torch.device('cpu')
        print(f"Using device: {device}")
        print("No GPU acceleration available")
    print()
    
    # Configuration
    config = {
        'num_classes': 52,  # 52 playing cards (expand later for jokers)
        'epochs': 20,       # Reduced for faster initial training
        'batch_size': 8,    # Smaller batch size for small dataset
        'learning_rate': 0.001,
        'model_type': 'resnet',  # 'resnet' or 'lightweight'
        'use_synthetic_data': False, # Use synthetic data from game assets
        'use_real_data': True,       # Use manually labeled screenshots
    }
    
    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    # Create model
    if config['model_type'] == 'resnet':
        model = CardClassifier(num_classes=config['num_classes'])
        print("Using ResNet18-based classifier")
    else:
        model = LightweightCardClassifier(num_classes=config['num_classes'])
        print("Using lightweight classifier")
    
    # Create trainer
    trainer = Trainer(model, device=device)
    
    # Log configuration
    trainer.logger.info("Training Configuration:")
    for key, value in config.items():
        trainer.logger.info(f"  {key}: {value}")
    
    # Create datasets
    datasets = []
    
    if config['use_synthetic_data']:
        print("Loading synthetic dataset from game assets...")
        synthetic_dataset = BalatroCardDataset(
            cards_dir="resources/textures/2x",
            augment_modifiers=False  # Start with just base cards
        )
        datasets.append(synthetic_dataset)
        print(f"Synthetic dataset: {len(synthetic_dataset)} samples")
    
    if config['use_real_data']:
        print("Loading real dataset from screenshots...")
        real_dataset = RealDatasetFromScreenshots()
        datasets.append(real_dataset)
        print(f"Real dataset: {len(real_dataset)} samples")
    
    # Combine datasets
    if len(datasets) == 0:
        print("Error: No datasets enabled")
        return
    elif len(datasets) == 1:
        dataset = datasets[0]
    else:
        # Combine multiple datasets
        from torch.utils.data import ConcatDataset
        dataset = ConcatDataset(datasets)
        print(f"Combined dataset: {len(dataset)} samples")
    
    # Start training
    print("\nStarting training...")
    history = trainer.train_card_classifier(
        dataset=dataset,
        epochs=config['epochs'],
        batch_size=config['batch_size'],
        learning_rate=config['learning_rate']
    )
    
    print("\nTraining completed!")
    print(f"Best validation accuracy: {max(history['val_acc']):.4f}")
    
    # Test the model
    print("\nTesting model on a few samples...")
    test_model(trainer.model, dataset, device)


def test_model(model, dataset, device, num_samples=5):
    """Test the trained model on a few samples"""
    model.eval()
    
    # Get a few random samples
    indices = torch.randperm(len(dataset))[:num_samples]
    
    with torch.no_grad():
        for i, idx in enumerate(indices):
            sample = dataset[idx]
            image = sample['image'].unsqueeze(0).to(device)  # Add batch dimension
            true_class = sample['card_class'].item()
            
            # Get prediction
            predicted_class, confidence = model.predict(image)
            predicted_class = predicted_class.item()
            confidence = confidence.item()
            
            print(f"Sample {i+1}:")
            print(f"  True class: {true_class}")
            print(f"  Predicted: {predicted_class}")
            print(f"  Confidence: {confidence:.4f}")
            print(f"  Correct: {'✓' if predicted_class == true_class else '✗'}")
            print()


if __name__ == "__main__":
    main()