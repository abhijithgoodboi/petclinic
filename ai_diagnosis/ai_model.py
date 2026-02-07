"""
AI Model Integration for Skin Disease Detection
Supports PyTorch (ResNet50) for cat skin disease classification
"""

import os
import time
from PIL import Image
from django.conf import settings

# Try importing PyTorch
PYTORCH_AVAILABLE = False
try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    PYTORCH_AVAILABLE = True
    print("PyTorch loaded successfully for AI diagnosis.")
except ImportError as e:
    print(f"PyTorch not available: {e}. AI predictions will use mock data.")

# Try importing numpy
try:
    import numpy as np
except ImportError:
    np = None


class CatSkinDiseaseDetector:
    """
    PyTorch-based detector using ResNet50 for cat skin diseases
    Trained on: Flea_Allergy, Health, Ringworm, Scabies
    """
    
    # Disease classes from the trained model (must match training order)
    DISEASE_CLASSES = ['Flea_Allergy', 'Health', 'Ringworm', 'Scabies']
    
    # Map model classes to our database disease categories
    DISEASE_MAPPING = {
        'Flea_Allergy': 'FLEA',
        'Health': 'HEALTHY',
        'Ringworm': 'RINGWORM',
        'Scabies': 'MANGE',  # Scabies is a type of mange
    }
    
    # Human-readable names
    DISEASE_DISPLAY_NAMES = {
        'Flea_Allergy': 'Flea Allergy Dermatitis',
        'Health': 'Healthy - No Disease Detected',
        'Ringworm': 'Ringworm (Dermatophytosis)',
        'Scabies': 'Scabies (Sarcoptic Mange)',
    }
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.model_version = 'v1.0-pytorch-resnet50-cat'
        self.device = None
        self.transform = None
        
        if PYTORCH_AVAILABLE:
            self._setup_device()
            self._setup_transforms()
            self._load_model()
    
    def _setup_device(self):
        """Setup CUDA or CPU device"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"AI Model using device: {self.device}")
    
    def _setup_transforms(self):
        """Setup image preprocessing transforms (must match training)"""
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def _load_model(self):
        """Load the pre-trained PyTorch ResNet50 model"""
        # Path to the model file
        model_path = os.path.join(settings.BASE_DIR, 'best_model_cat.pth')
        
        if not os.path.exists(model_path):
            print(f"Model file not found at {model_path}. Using mock predictions.")
            self.model_loaded = False
            return
        
        try:
            # Create ResNet50 architecture
            self.model = models.resnet50(weights=None)
            num_ftrs = self.model.fc.in_features
            self.model.fc = nn.Linear(num_ftrs, len(self.DISEASE_CLASSES))
            
            # Load trained weights
            self.model.load_state_dict(
                torch.load(model_path, map_location=self.device)
            )
            
            # Move to device and set to evaluation mode
            self.model = self.model.to(self.device)
            self.model.eval()
            
            self.model_loaded = True
            print(f"Cat Skin Disease Model loaded successfully from {model_path}")
            print(f"Classes: {self.DISEASE_CLASSES}")
            
        except Exception as e:
            print(f"Error loading PyTorch model: {e}")
            self.model_loaded = False
    
    def preprocess_image(self, image_path):
        """Load and preprocess image for inference"""
        try:
            image = Image.open(image_path).convert("RGB")
            image_tensor = self.transform(image).unsqueeze(0)  # Add batch dimension
            return image_tensor.to(self.device)
        except Exception as e:
            raise Exception(f"Error preprocessing image: {e}")
    
    def predict(self, image_path):
        """
        Make prediction on an image
        Returns dict with disease prediction and confidence scores
        """
        start_time = time.time()
        
        try:
            if self.model_loaded and self.model is not None:
                # Preprocess image
                image_tensor = self.preprocess_image(image_path)
                
                # Make prediction
                with torch.no_grad():
                    outputs = self.model(image_tensor)
                    probabilities = torch.softmax(outputs, dim=1)
                    probabilities = probabilities.cpu().numpy()[0]
                
            else:
                # Mock predictions for demonstration
                probabilities = self._generate_mock_predictions()
            
            # Get indices sorted by probability (highest first)
            sorted_indices = np.argsort(probabilities)[::-1]
            
            # Primary prediction
            primary_idx = sorted_indices[0]
            primary_class = self.DISEASE_CLASSES[primary_idx]
            primary_confidence = float(probabilities[primary_idx])
            
            # Map to database disease category
            mapped_disease = self.DISEASE_MAPPING.get(primary_class, primary_class.upper())
            
            # Build alternatives list
            alternatives = []
            for idx in sorted_indices[1:]:
                alt_class = self.DISEASE_CLASSES[idx]
                alternatives.append({
                    'disease': self.DISEASE_MAPPING.get(alt_class, alt_class.upper()),
                    'disease_name': self.DISEASE_DISPLAY_NAMES.get(alt_class, alt_class),
                    'confidence': float(probabilities[idx])
                })
            
            processing_time = time.time() - start_time
            
            results = {
                'primary_disease': mapped_disease,
                'primary_disease_name': self.DISEASE_DISPLAY_NAMES.get(primary_class, primary_class),
                'primary_confidence': primary_confidence,
                'alternatives': alternatives,
                'processing_time': processing_time,
                'model_version': self.model_version,
                'raw_class': primary_class,
                'all_probabilities': {
                    self.DISEASE_CLASSES[i]: float(probabilities[i])
                    for i in range(len(self.DISEASE_CLASSES))
                }
            }
            
            return results
            
        except Exception as e:
            raise Exception(f"Error making prediction: {e}")
    
    def _generate_mock_predictions(self):
        """Generate mock probabilities for testing when model isn't available"""
        if np is None:
            # Fallback if numpy not available
            import random
            probs = [random.random() for _ in self.DISEASE_CLASSES]
            total = sum(probs)
            return [p / total for p in probs]
        
        probs = np.random.dirichlet(np.ones(len(self.DISEASE_CLASSES)) * 2)
        # Make one class dominant
        dominant_idx = np.random.randint(0, len(self.DISEASE_CLASSES))
        probs[dominant_idx] += 0.4
        probs = probs / probs.sum()
        return probs
    
    def get_treatment_recommendations(self, disease):
        """Get treatment recommendations from database or defaults"""
        from .models import TreatmentRecommendation
        
        try:
            treatment = TreatmentRecommendation.objects.get(disease=disease)
            return {
                'description': treatment.description,
                'symptoms': treatment.symptoms,
                'causes': treatment.causes,
                'home_care': treatment.home_care,
                'medical_treatment': treatment.medical_treatment,
                'prevention': treatment.prevention,
                'recovery_time': treatment.recovery_time,
                'contagious': treatment.contagious,
            }
        except TreatmentRecommendation.DoesNotExist:
            return self._get_default_recommendations(disease)
    
    def _get_default_recommendations(self, disease):
        """Default recommendations for diseases not in database"""
        
        recommendations = {
            'FLEA': {
                'description': 'Flea Allergy Dermatitis (FAD) is an allergic reaction to flea saliva.',
                'symptoms': 'Intense itching, hair loss, red skin, small bumps, especially near tail base and hindquarters.',
                'causes': 'Allergic reaction to proteins in flea saliva. Even one flea bite can trigger severe reaction.',
                'home_care': 'Flea comb daily, wash bedding in hot water, vacuum frequently, apply vet-approved flea treatment.',
                'medical_treatment': 'Prescription flea prevention, antihistamines, corticosteroids for inflammation, antibiotics if secondary infection.',
                'prevention': 'Year-round flea prevention, regular grooming, treat all pets in household, environmental flea control.',
                'recovery_time': '2-4 weeks with proper flea control and treatment',
                'contagious': False,
            },
            'HEALTHY': {
                'description': 'No skin disease detected. Your pet appears to have healthy skin.',
                'symptoms': 'No visible symptoms of skin disease.',
                'causes': 'N/A - Pet is healthy.',
                'home_care': 'Continue regular grooming and skin checks. Maintain good nutrition.',
                'medical_treatment': 'No treatment needed. Regular wellness check-ups recommended.',
                'prevention': 'Regular grooming, balanced diet, flea/tick prevention, routine vet visits.',
                'recovery_time': 'N/A',
                'contagious': False,
            },
            'RINGWORM': {
                'description': 'Ringworm is a fungal infection (not a worm) that affects skin, hair, and nails.',
                'symptoms': 'Circular patches of hair loss, scaly/crusty skin, red rings, brittle/broken hair.',
                'causes': 'Fungal infection (Microsporum or Trichophyton species) spread by direct contact or contaminated objects.',
                'home_care': 'Isolate infected pet, wear gloves when handling, disinfect environment, wash hands thoroughly.',
                'medical_treatment': 'Topical antifungal creams/shampoos, oral antifungal medication (griseofulvin, itraconazole), lime sulfur dips.',
                'prevention': 'Quarantine new pets, regular cleaning, avoid contact with infected animals, boost immune system.',
                'recovery_time': '6-8 weeks with treatment, sometimes longer',
                'contagious': True,
            },
            'MANGE': {
                'description': 'Scabies (Sarcoptic Mange) is caused by microscopic mites burrowing into the skin.',
                'symptoms': 'Intense itching, red skin, hair loss, crusty sores, especially on ears, elbows, and abdomen.',
                'causes': 'Sarcoptes scabiei mites that burrow into skin. Highly contagious through direct contact.',
                'home_care': 'Isolate pet, wash all bedding, treat all pets in household, wear gloves (can temporarily affect humans).',
                'medical_treatment': 'Prescription anti-parasitic medication (ivermectin, selamectin), medicated baths, antibiotics for secondary infections.',
                'prevention': 'Avoid contact with infected animals, regular vet check-ups, maintain good hygiene.',
                'recovery_time': '4-6 weeks with aggressive treatment',
                'contagious': True,
            },
        }
        
        if disease in recommendations:
            return recommendations[disease]
        
        return {
            'description': f'Detected condition: {disease}',
            'symptoms': 'Please consult with a veterinarian for detailed information.',
            'causes': 'Multiple factors may contribute to this condition.',
            'home_care': 'Keep the affected area clean and monitor your pet closely.',
            'medical_treatment': 'Professional veterinary care is recommended.',
            'prevention': 'Regular check-ups and proper hygiene can help prevent issues.',
            'recovery_time': 'Varies depending on severity and treatment',
            'contagious': False,
        }


# Singleton instance
_detector_instance = None


def get_detector():
    """Get or create the singleton detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = CatSkinDiseaseDetector()
    return _detector_instance


def analyze_skin_image(image_path):
    """
    Analyze a skin image and return diagnosis results
    
    Args:
        image_path: Path to the image file
        
    Returns:
        dict with prediction results
    """
    detector = get_detector()
    return detector.predict(image_path)


def get_treatment_info(disease):
    """
    Get treatment recommendations for a disease
    
    Args:
        disease: Disease code (e.g., 'RINGWORM', 'FLEA', 'MANGE', 'HEALTHY')
        
    Returns:
        dict with treatment information
    """
    detector = get_detector()
    return detector.get_treatment_recommendations(disease)


def is_model_loaded():
    """Check if the AI model is loaded and ready"""
    detector = get_detector()
    return detector.model_loaded


def get_model_info():
    """Get information about the loaded model"""
    detector = get_detector()
    return {
        'loaded': detector.model_loaded,
        'version': detector.model_version,
        'device': str(detector.device) if detector.device else 'N/A',
        'classes': detector.DISEASE_CLASSES,
        'pytorch_available': PYTORCH_AVAILABLE,
    }
