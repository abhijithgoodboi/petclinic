"""
AI Model Integration for Skin Disease Detection
This module handles the loading and inference of the AI model
"""

import os
import time
import numpy as np
import cv2  # Added OpenCV for high-quality preprocessing
from PIL import Image
from django.conf import settings

# Try importing TensorFlow/Keras
try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError as e:
    TF_AVAILABLE = False
    print(f"TensorFlow/Keras Load Error: {e}. AI predictions will use mock data.")


class SkinDiseaseDetector:
    """AI model wrapper using CNN (Keras) and OpenCV preprocessing"""
    
    DISEASE_CLASSES = [
        'HEALTHY',
        'RINGWORM',
        'MANGE',
        'DERMATITIS',
        'HOT_SPOT',
        'ALLERGY',
        'FUNGAL',
        'BACTERIAL',
        'FLEA',
        'ECZEMA',
    ]
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.model_version = 'v1.0-cnn-keras-opencv'
        self.input_shape = (224, 224)  # Standard CNN input size
        
        if TF_AVAILABLE:
            self.load_model()
    
    def load_model(self):
        """Load the pre-trained Keras CNN model"""
        model_path = settings.AI_MODEL_PATH
        
        if os.path.exists(model_path):
            try:
                self.model = keras.models.load_model(model_path)
                self.model_loaded = True
                print(f"CNN Model loaded successfully from {model_path}")
            except Exception as e:
                print(f"Error loading Keras model: {e}")
                self.model_loaded = False
        else:
            print(f"Model file not found at {model_path}. Using mock logic.")
            self.model_loaded = False
    
    def preprocess_image(self, image_path):
        """
        Preprocess image using OpenCV for better CNN accuracy
        """
        try:
            # 1. Load image with OpenCV
            img = cv2.imread(image_path)
            if img is None:
                raise Exception("OpenCV could not read the image.")

            # 2. Convert BGR (OpenCV default) to RGB (CNN requirement)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 3. Resize using Inter-Area interpolation (best for shrinking)
            img = cv2.resize(img, self.input_shape, interpolation=cv2.INTER_AREA)
            
            # 4. Normalize pixel values (0 to 1)
            img_array = img.astype('float32') / 255.0
            
            # 5. Add batch dimension for Keras
            img_array = np.expand_dims(img_array, axis=0)
            
            return img_array
        
        except Exception as e:
            # Fallback to PIL if OpenCV fails
            print(f"OpenCV Preprocessing failed, falling back to PIL: {e}")
            img = Image.open(image_path).convert('RGB').resize(self.input_shape)
            return np.expand_dims(np.array(img).astype('float32') / 255.0, axis=0)
    
    def predict(self, image_path):
        """
        Make prediction on an image
        """
        start_time = time.time()
        
        try:
            # Preprocess image
            img_array = self.preprocess_image(image_path)
            
            # Make prediction
            if self.model_loaded and self.model is not None:
                predictions = self.model.predict(img_array, verbose=0)
                probabilities = predictions[0]
            else:
                # Mock predictions for demonstration
                probabilities = self._generate_mock_predictions()
            
            # Get top 4 predictions
            top_indices = np.argsort(probabilities)[-4:][::-1]
            
            results = {
                'primary_disease': self.DISEASE_CLASSES[top_indices[0]],
                'primary_confidence': float(probabilities[top_indices[0]]),
                'alternatives': [
                    {
                        'disease': self.DISEASE_CLASSES[idx],
                        'confidence': float(probabilities[idx])
                    }
                    for idx in top_indices[1:4]
                ],
                'processing_time': time.time() - start_time,
                'model_version': self.model_version,
                'all_probabilities': {
                    self.DISEASE_CLASSES[i]: float(probabilities[i])
                    for i in range(len(self.DISEASE_CLASSES))
                }
            }
            
            return results
        
        except Exception as e:
            raise Exception(f"Error making prediction: {e}")
    
    def _generate_mock_predictions(self):
        """Generate mock probabilities that sum to 1"""
        probs = np.random.dirichlet(np.ones(len(self.DISEASE_CLASSES)) * 2)
        dominant_idx = np.random.randint(0, len(self.DISEASE_CLASSES))
        probs[dominant_idx] += 0.3
        probs = probs / probs.sum()
        return probs
    
    def get_treatment_recommendations(self, disease):
        """Get recommendations from database or defaults"""
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
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SkinDiseaseDetector()
    return _detector_instance

def analyze_skin_image(image_path):
    detector = get_detector()
    return detector.predict(image_path)

def get_treatment_info(disease):
    detector = get_detector()
    return detector.get_treatment_recommendations(disease)