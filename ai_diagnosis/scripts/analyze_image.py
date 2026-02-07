#!/usr/bin/env python3
"""
External Image Analysis Script for Ernakulam Pet Hospital
=========================================================

This script uses the trained PyTorch ResNet50 model to classify cat skin diseases.

Usage:
    python analyze_image.py /path/to/image.jpg

Output Format (JSON):
{
    "primary_disease": "RINGWORM",
    "primary_confidence": 0.9969,
    "alternatives": [...],
    "processing_time": 0.05,
    "model_version": "pytorch-resnet50-cat"
}
"""

import sys
import json
import time
import os

# PyTorch imports
try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    from PIL import Image
    PYTORCH_AVAILABLE = True
except ImportError as e:
    PYTORCH_AVAILABLE = False
    IMPORT_ERROR = str(e)


# Disease class mapping
# Model classes -> Database disease codes
CLASS_NAMES = ['Flea_Allergy', 'Health', 'Ringworm', 'Scabies']
DISEASE_MAPPING = {
    'Flea_Allergy': 'FLEA',
    'Health': 'HEALTHY',
    'Ringworm': 'RINGWORM',
    'Scabies': 'MANGE',
}


def get_model_path():
    """Get path to the model file"""
    # Try different locations
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(script_dir, '..', '..', 'best_model_cat.pth'),  # Project root
        os.path.join(script_dir, 'best_model_cat.pth'),  # Same dir as script
        '/home/anastasia/gits/veterinary_platform/best_model_cat.pth',  # Absolute path
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    return None


def load_model():
    """Load the PyTorch ResNet50 model"""
    model_path = get_model_path()
    
    if model_path is None:
        raise FileNotFoundError("Model file 'best_model_cat.pth' not found")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Create model architecture
    model = models.resnet50(weights=None)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, len(CLASS_NAMES))
    
    # Load trained weights
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    
    return model, device


def get_transform():
    """Get image preprocessing transform (must match training)"""
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])


def analyze_image(image_path):
    """
    Analyze the image using PyTorch model
    
    Args:
        image_path: Full path to the image file
        
    Returns:
        dict: Prediction results
    """
    start_time = time.time()
    
    # Verify image exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    if not PYTORCH_AVAILABLE:
        raise ImportError(f"PyTorch not available: {IMPORT_ERROR}")
    
    # Load model
    model, device = load_model()
    transform = get_transform()
    
    # Load and preprocess image
    image = Image.open(image_path).convert("RGB")
    image_tensor = transform(image).unsqueeze(0).to(device)
    
    # Run inference
    with torch.no_grad():
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)
        probabilities = probabilities.cpu().numpy()[0]
    
    # Get sorted indices (highest probability first)
    sorted_indices = probabilities.argsort()[::-1]
    
    # Primary prediction
    primary_idx = sorted_indices[0]
    primary_class = CLASS_NAMES[primary_idx]
    primary_confidence = float(probabilities[primary_idx])
    
    # Map to database disease code
    primary_disease = DISEASE_MAPPING.get(primary_class, primary_class.upper())
    
    # Build alternatives
    alternatives = []
    for idx in sorted_indices[1:]:
        alt_class = CLASS_NAMES[idx]
        alt_disease = DISEASE_MAPPING.get(alt_class, alt_class.upper())
        alternatives.append({
            'disease': alt_disease,
            'confidence': float(probabilities[idx])
        })
    
    processing_time = time.time() - start_time
    
    result = {
        'primary_disease': primary_disease,
        'primary_confidence': round(primary_confidence, 4),
        'alternatives': alternatives,
        'processing_time': round(processing_time, 3),
        'model_version': 'pytorch-resnet50-cat-v1.0',
        'raw_class': primary_class,
        'all_probabilities': {
            CLASS_NAMES[i]: float(probabilities[i])
            for i in range(len(CLASS_NAMES))
        },
        'metadata': {
            'image_path': image_path,
            'device': str(device),
            'script_version': '2.0.0'
        }
    }
    
    return result


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'No image path provided',
            'usage': 'python analyze_image.py /path/to/image.jpg'
        }))
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        result = analyze_image(image_path)
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        print(json.dumps({
            'error': str(e),
            'image_path': image_path
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()
