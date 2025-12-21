# Balatro Card Recognition - YOLO Training Guide

## Overview

This document covers the YOLOv8-based training pipeline for Balatro card recognition. The system uses pre-labeled Roboflow datasets to train production-ready object detection models for robust card and game element detection.

## Architecture

### YOLO-Based Approach
1. **YOLOv8 Object Detection**: Real-time detection of cards, jokers, and game elements
2. **85-Class Detection**: Playing cards (52) + jokers + consumables + enhancements + game elements
3. **Hybrid Pipeline**: YOLOv8 primary + template matching fallback + traditional CV backup

### Models Available
- **YOLOv8n**: Nano model for speed (recommended for real-time)
- **YOLOv8s**: Small model for balanced speed/accuracy
- **YOLOv8m**: Medium model for higher accuracy
- **YOLOv8l**: Large model for maximum accuracy

## File Structure

```
dataset/
├── labeled/               # YOLO formatted datasets from Roboflow
│   └── Cards.v7-v1.2.1-2025-12-20-gen52-hc--backg.yolov8/
│       ├── train/
│       │   ├── images/    # Training images
│       │   └── labels/    # YOLO format labels (.txt)
│       ├── valid/
│       │   ├── images/    # Validation images
│       │   └── labels/    # YOLO format labels (.txt)
│       ├── test/
│       │   ├── images/    # Test images
│       │   └── labels/    # YOLO format labels (.txt)
│       └── data.yaml      # Dataset configuration
├── raw/                   # Original screenshots for testing
└── debug_cards/           # Extracted cards for development

src/vision/
├── card_detector.py       # YOLOv8-based card detection
├── template_matcher.py    # Template matching fallback
├── hybrid_detector.py     # Multi-method ensemble detection
└── card_recognizer.py     # Legacy compatibility wrapper

Training Scripts:
├── train_yolo_model.py    # Main YOLO training script
├── src/ml/setup_ml.py     # Environment setup for YOLO
└── dataset/generate_variants.py  # Synthetic data augmentation

Models:
└── models/                # Trained YOLO model checkpoints
    └── balatro_cards/
        └── weights/
            ├── best.pt    # Best validation model
            └── last.pt    # Latest checkpoint
```

## Setup Instructions

### 1. Environment Setup
```bash
# Check system and install YOLO dependencies
python src/ml/setup_ml.py

# Install YOLOv8 and dependencies
pip install ultralytics torch opencv-python pillow pyyaml matplotlib

# Verify GPU setup
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### 2. Dataset Verification

The system uses pre-labeled Roboflow datasets in YOLO format:

```bash
# Check dataset structure
python src/ml/setup_ml.py

# Expected output:
# ✓ YOLO dataset found
#   Classes: 85
#   Names: 85 total
#   Train: 1234 images
#   Valid: 234 images
#   Test: 123 images
```

**85-Class Dataset Structure:**
- **Playing Cards (52)**: 10C, 10D, 10H, 10S, 2C, 2D, ..., AS
- **Jokers**: Abstract-Joker, Blueprint, Brainstorm, Chaos-the-Clown, etc.
- **Consumables**: Tarot cards, Planet cards, Spectral cards
- **Game Elements**: Deck, Enhancement, Seal, Stone, etc.
- **Shop Items**: Tags, Booster packs, etc.

### 3. Training

```bash
# Train YOLOv8 model on Balatro dataset
python train_yolo_model.py

# Test trained model
python train_yolo_model.py --test

# Test specific model
python train_yolo_model.py --test models/balatro_cards/weights/best.pt
```

## Model Details

### YOLOv8 Architecture
- **Input**: Variable size images (auto-resized to 640x640 during training)
- **Architecture**: YOLOv8 backbone with detection head
- **Output**: Bounding boxes + class probabilities + confidence scores
- **Training**: Multi-part loss (box regression + classification + objectness)
- **Augmentation**: Mosaic, mixup, rotation, scaling, color jitter

### Model Variants
- **YOLOv8n (Nano)**: 3.2M parameters, ~37ms inference (CPU)
- **YOLOv8s (Small)**: 11.2M parameters, ~44ms inference (CPU)  
- **YOLOv8m (Medium)**: 25.9M parameters, ~50ms inference (CPU)
- **YOLOv8l (Large)**: 43.7M parameters, ~57ms inference (CPU)

### Detection Pipeline
1. **Image Preprocessing**: Resize, normalize, letterbox padding
2. **Inference**: Forward pass through YOLOv8 model
3. **Post-processing**: Non-Maximum Suppression (NMS)
4. **Output**: List of detections with [x1, y1, x2, y2, confidence, class_id]

## Training Process

### Training Configuration
```python
config = {
    'model': 'yolov8n.pt',     # Pre-trained model to start from
    'epochs': 100,             # Training epochs
    'batch': 16,               # Batch size
    'imgsz': 640,              # Image size
    'device': 'auto',          # Auto-detect GPU/CPU
    'patience': 20,            # Early stopping patience
    'optimizer': 'AdamW',      # Optimizer
    'lr0': 0.01,               # Initial learning rate
    'weight_decay': 0.0005,    # Weight decay
    'box': 7.5,                # Box loss gain
    'cls': 0.5,                # Class loss gain
    'dfl': 1.5,                # DFL loss gain
}
```

### Automatic Features
- **GPU Detection**: Automatically uses CUDA if available
- **Model Checkpointing**: Saves best model based on validation mAP
- **Learning Rate Scheduling**: Cosine annealing with warmup
- **Early Stopping**: Stops training if no improvement for `patience` epochs
- **Validation Metrics**: mAP@0.5, mAP@0.5:0.95, precision, recall

### Training Output
```
=== YOLOv8 Balatro Card Training ===

📊 Dataset: 85 classes
🎯 Classes: 85 total
🚀 Starting YOLOv8 training...
Model: yolov8n.pt
Epochs: 100
Batch size: 16
Image size: 640

Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
  1/100      1.2G      1.234      2.345      1.567        123        640
  2/100      1.2G      1.123      2.234      1.456        123        640
  ...
 50/100      1.2G      0.456      0.789      0.234        123        640

✅ Training completed successfully!
📁 Model saved to: models/balatro_cards/
🎯 Best model: models/balatro_cards/weights/best.pt

🔍 Running validation...
📊 Validation Results:
   mAP50: 0.892
   mAP50-95: 0.654
   Precision: 0.876
   Recall: 0.834
```

## Performance Expectations

### With Pre-labeled Roboflow Dataset
- **Accuracy**: 85-95% mAP@0.5 expected (production ready)
- **Training Time**: 2-4 hours on GPU (100 epochs)
- **Use Case**: Production deployment with real-time inference

### Real-time Performance
- **YOLOv8n**: 37-57ms per image (CPU), <20ms (GPU)
- **Multi-object Detection**: Detects all cards in single pass (1-8 cards per hand)
- **Confidence Scoring**: Threshold-based filtering with fallback mechanisms
- **GPU Acceleration**: Automatic CUDA detection for faster processing

### Inference Benchmarks
- **Detection Speed**: <50ms per screenshot
- **Batch Processing**: Can process multiple images simultaneously
- **Memory Usage**: ~2GB VRAM during training, ~500MB during inference
- **Accuracy**: >90% detection rate on Balatro screenshots

## Troubleshooting

### Common Issues

**Low mAP (<70%)**
- Insufficient training epochs
- Learning rate too high/low
- Class imbalance in dataset
- Solution: Train longer, adjust hyperparameters, check dataset balance

**Overfitting (Train mAP >> Val mAP)**
- Too many epochs without early stopping
- Model too complex for dataset size
- Solution: Enable early stopping, use data augmentation, reduce model size

**GPU Out of Memory**
- Reduce batch size from 16 to 8 or 4
- Use smaller model (yolov8n instead of yolov8s)
- Reduce image size from 640 to 416

**Poor Detection Performance**
- Check confidence threshold (try 0.3-0.7)
- Verify NMS threshold (try 0.4-0.6)
- Test with different model variants

### Debugging Tools

```bash
# Test YOLO setup
python src/ml/setup_ml.py

# Test trained model on sample images
python train_yolo_model.py --test

# Test vision pipeline
python test_vision.py screenshot.png

# Process screenshots with enhanced detection
python src/tools/improved_screenshot_processor.py dataset/raw/screenshot.png --debug
```

## Integration with Vision Pipeline

### Hybrid Detection System
The trained YOLO model integrates with the existing hybrid detection pipeline:

```python
# Primary: YOLOv8 detection
from ultralytics import YOLO
model = YOLO('models/balatro_cards/weights/best.pt')
results = model(screenshot)

# Fallback: Template matching for low-confidence detections
if confidence < 0.7:
    template_result = template_matcher.match(card_region)

# Backup: Traditional CV methods
if template_confidence < 0.5:
    cv_result = traditional_cv_detector.detect(card_region)
```

### Real-time Inference
- **Preprocessing**: Automatic image resizing and normalization
- **Batch Processing**: Process multiple screenshots simultaneously  
- **Confidence Thresholding**: Reject low-confidence predictions (< 0.5)
- **Non-Maximum Suppression**: Remove overlapping detections
- **Coordinate Conversion**: Convert bounding boxes to game coordinates

### Performance Benchmarks
- **YOLOv8n**: ~37ms per image (CPU), ~15ms (GPU)
- **YOLOv8s**: ~44ms per image (CPU), ~18ms (GPU)
- **Memory Usage**: ~500MB VRAM during inference
- **Batch Processing**: Can process 4-8 images simultaneously for better throughput

## Alignment with Building AI Plan

This YOLO-based training pipeline directly supports **Phase 3: Enhanced Card Detection** from the Building AI Plan:

### Phase 3.1: Advanced Computer Vision Card Detection ✅
- **YOLOv8-based card detection** trained specifically for Balatro cards
- **Enhanced template matching** using game sprites with rotation/scale invariance  
- **Hybrid detection pipeline** combining deep learning + template matching + traditional CV
- **Card region refinement** for exact boundaries and quality assessment

### Phase 3.2: Production Integration 🚧
- **Nova-assisted validation** for continuous model improvement
- **Active learning pipeline** for dataset expansion
- **Custom model training** on Balatro-specific data
- **Performance optimization** with GPU acceleration

### Success Metrics
- **>95% detection accuracy**: Achievable with pre-labeled Roboflow dataset
- **<500ms processing time**: YOLOv8n provides <50ms inference
- **<2% false positives**: Confidence thresholding and NMS reduce false detections

## Future Improvements

### Short Term (Phase 3 Completion)
- **Model Optimization**: Fine-tune hyperparameters for Balatro-specific performance
- **Confidence Calibration**: Optimize thresholds for hybrid pipeline integration
- **Performance Benchmarking**: Comprehensive testing on diverse Balatro screenshots

### Long Term (Phase 4: AI Pipeline Foundation)
- **Nova Integration**: Use Amazon Nova for state extraction from detected cards
- **Policy Agent Training**: Convert detected cards to canonical game state JSON
- **Reinforcement Learning**: Train agent to play optimally using detected game state
- **Real-time Gameplay**: Live analysis and strategy recommendations

## Change Log

### 2025-12-20
- **Complete Restructuring**: Updated from PyTorch CNN approach to YOLOv8 object detection
- **Roboflow Integration**: Aligned with pre-labeled 85-class dataset from Roboflow
- **Hybrid Pipeline**: Integrated with existing template matching and traditional CV fallbacks
- **Production Focus**: Optimized for real-time inference and deployment
- **Building AI Plan Alignment**: Directly supports Phase 3 enhanced card detection objectives
