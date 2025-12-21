#!/usr/bin/env python3
"""
Setup ML Environment - Check dependencies and prepare for YOLO training
"""

import sys
import subprocess
from pathlib import Path


def check_yolo():
    """Check YOLOv8 installation and dependencies"""
    try:
        from ultralytics import YOLO
        import ultralytics
        
        print(f"✓ Ultralytics {ultralytics.__version__}")
        
        # Test YOLO model loading
        try:
            model = YOLO('yolov8n.pt')  # This will download if not present
            print("✓ YOLOv8 model loading successful")
        except Exception as e:
            print(f"⚠ YOLOv8 model test failed: {e}")
        
        return True
    except ImportError as e:
        print(f"✗ YOLOv8 not installed: {e}")
        return False


def check_dependencies():
    """Check all required dependencies"""
    required = [
        'ultralytics', 'torch', 'numpy', 'matplotlib', 
        'opencv-python', 'pillow', 'pyyaml'
    ]
    
    missing = []
    for package in required:
        try:
            if package == 'opencv-python':
                import cv2
                print(f"✓ opencv-python (cv2 {cv2.__version__})")
            elif package == 'pillow':
                from PIL import Image
                print(f"✓ pillow (PIL)")
            elif package == 'pyyaml':
                import yaml
                print(f"✓ pyyaml")
            else:
                module = __import__(package)
                if hasattr(module, '__version__'):
                    print(f"✓ {package} {module.__version__}")
                else:
                    print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package}")
            missing.append(package)
    
    return len(missing) == 0, missing


def check_gpu():
    """Check GPU availability for training"""
    try:
        import torch
        
        if torch.cuda.is_available():
            print(f"✓ CUDA {torch.version.cuda}")
            print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
            print(f"✓ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
            return "cuda"
        elif torch.backends.mps.is_available():
            print("✓ MPS (Metal Performance Shaders) available")
            print("✓ GPU: Apple Silicon (M-series chip)")
            return "mps"
        else:
            print("⚠ No GPU acceleration available - will use CPU")
            return "cpu"
    except ImportError:
        print("⚠ PyTorch not available - GPU detection skipped")
        return "unknown"


def setup_directories():
    """Create necessary directories"""
    dirs = [
        "dataset/labeled",
        "dataset/raw", 
        "dataset/debug_cards",
        "models",
        "logs"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {dir_path}")


def check_yolo_dataset():
    """Check if YOLO dataset is available"""
    dataset_path = Path("dataset/labeled/Cards.v7-v1.2.1-2025-12-20-gen52-hc--backg.yolov8")
    data_yaml = dataset_path / "data.yaml"
    
    if data_yaml.exists():
        try:
            import yaml
            with open(data_yaml, 'r') as f:
                config = yaml.safe_load(f)
            
            print(f"✓ YOLO dataset found")
            print(f"  Classes: {config.get('nc', 'Unknown')}")
            print(f"  Names: {len(config.get('names', []))} total")
            
            # Check splits
            for split in ['train', 'valid', 'test']:
                split_path = dataset_path / split / 'images'
                if split_path.exists():
                    count = len(list(split_path.glob('*.jpg')) + list(split_path.glob('*.png')))
                    print(f"  {split.capitalize()}: {count} images")
                else:
                    print(f"  {split.capitalize()}: Missing")
            
            return True
        except Exception as e:
            print(f"✗ YOLO dataset error: {e}")
            return False
    else:
        print("✗ YOLO dataset not found")
        print(f"  Expected: {data_yaml}")
        return False


def install_yolo():
    """Install YOLOv8 and dependencies"""
    print("Installing YOLOv8 and dependencies...")
    
    packages = [
        "ultralytics",
        "torch", 
        "torchvision",
        "opencv-python",
        "pillow",
        "pyyaml",
        "matplotlib"
    ]
    
    try:
        for package in packages:
            print(f"Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
        
        print("✓ YOLOv8 dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False


def main():
    """Main setup function"""
    print("=== Balatro YOLO Training Setup ===\n")
    
    # Check dependencies
    print("Checking dependencies...")
    deps_ok, missing = check_dependencies()
    
    if not deps_ok:
        print(f"\nMissing dependencies: {missing}")
        
        response = input("\nInstall missing dependencies? (y/n): ")
        if response.lower() == 'y':
            if install_yolo():
                deps_ok = True
            else:
                return
        else:
            print("Please install dependencies manually:")
            print("pip install ultralytics torch opencv-python pillow pyyaml matplotlib")
            return
    
    print("\n" + "="*50)
    
    # Check YOLOv8 specifically
    print("Checking YOLOv8...")
    yolo_ok = check_yolo()
    
    print("\n" + "="*50)
    
    # Check GPU
    print("Checking GPU support...")
    gpu_type = check_gpu()
    
    print("\n" + "="*50)
    
    # Setup directories
    print("Setting up directories...")
    setup_directories()
    
    print("\n" + "="*50)
    
    # Check YOLO dataset
    print("Checking YOLO dataset...")
    dataset_ok = check_yolo_dataset()
    
    print("\n" + "="*50)
    
    # Summary
    print("Setup Summary:")
    print(f"✓ Dependencies: {'OK' if deps_ok else 'Missing'}")
    print(f"✓ YOLOv8: {'OK' if yolo_ok else 'Missing'}")
    print(f"✓ GPU: {gpu_type}")
    print(f"✓ Dataset: {'OK' if dataset_ok else 'Missing'}")
    
    if deps_ok and yolo_ok and dataset_ok:
        print("\n🎉 Ready to start YOLO training!")
        print("\nNext steps:")
        print("1. Run: python train_yolo_model.py")
        print("2. Test: python train_yolo_model.py --test")
    else:
        print("\n⚠ Setup incomplete. Please resolve issues above.")
        if not dataset_ok:
            print("\nTo get the dataset:")
            print("1. Export from Roboflow in YOLOv8 format")
            print("2. Extract to dataset/labeled/")


if __name__ == "__main__":
    main()