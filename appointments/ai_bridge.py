"""
AI Bridge Module for Veterinary Platform
========================================
This module provides a unified interface to call:
1. JSON Symptom Matcher - Fast pattern matching with predefined emergency cases
2. Groq AI - Symptom assessment (text → priority classification)
3. PyTorch Model - Skin disease detection (image → diagnosis)

Priority Order:
1. JSON Matcher (instant response for known emergency patterns)
2. Groq AI (for complex/unknown symptoms)
3. Keyword Fallback (if Groq fails)

Usage:
    from appointments.ai_bridge import analyze_symptoms, analyze_skin_image, get_full_assessment
"""

import os
import json
import re
from typing import Dict, Tuple, Optional, Any
from django.conf import settings

# Import JSON Symptom Matcher
try:
    from .json_symptom_matcher import match_symptoms as json_match_symptoms
    JSON_MATCHER_AVAILABLE = True
except ImportError:
    JSON_MATCHER_AVAILABLE = False
    print("Warning: JSON Symptom Matcher not available.")

# ============================================================================
# GROQ AI SYMPTOM ANALYZER
# ============================================================================

GROQ_AVAILABLE = False
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    print("Groq package not installed. Symptom AI will use fallback.")


# Groq API Configuration
# Get key from environment variable or django settings
# Example: export GROQ_API_KEY="your-api-key-here"
import os
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"


def analyze_symptoms_with_groq(symptoms: str, pet_id: str = None) -> Dict[str, Any]:
    """
    Analyze pet symptoms to classify priority.
    
    Priority Order:
    1. JSON Matcher - Check predefined emergency patterns first
    2. Groq AI - For complex/unknown symptoms
    3. Keyword Fallback - If Groq fails
    
    Args:
        symptoms: Text description of pet symptoms
        pet_id: Optional pet identifier
        
    Returns:
        Dict with category, reason, and raw assessment
    """
    if not symptoms or not symptoms.strip():
        return {
            'success': False,
            'category': 'NORMAL',
            'priority': 'NORMAL',
            'reason': 'No symptoms provided',
            'assessment': '',
        }
    
    # Step 1: Check JSON Matcher first (instant response for known patterns)
    if JSON_MATCHER_AVAILABLE:
        json_result = json_match_symptoms(symptoms, pet_id)
        if json_result.get('matched'):
            # Map JSON result to our format
            priority = json_result.get('priority', 'NORMAL')
            category_map = {
                'EMERGENCY': 'Emergency',
                'HIGH': 'Urgent',
                'NORMAL': 'Routine',
                'LOW': 'Routine',
            }
            return {
                'success': True,
                'category': category_map.get(priority, 'Routine'),
                'priority': priority,
                'reason': json_result.get('reason', ''),
                'assessment': json_result.get('full_assessment', ''),
                'pet_id': json_result.get('pet_id', pet_id),
                'symptoms': symptoms,
                'model': 'json_symptom_matcher',
                'json_match_score': json_result.get('match_score', 0),
            }
    
    # Step 2: Use Groq AI for unknown symptoms
    if GROQ_AVAILABLE:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional veterinary triage assistant. Be concise and accurate."
                    },
                    {
                        "role": "user",
                        "content": f"""
Classify the following pet symptoms into ONLY ONE category:

1. Emergency – life-threatening, needs immediate vet care
2. Urgent – needs vet care soon (within 24 hours)
3. Routine – can be monitored or handled with basic care

Give a short reason (one line only).

Respond strictly in this format:
Category: <Emergency/Urgent/Routine>
Reason: <one-line explanation>

Symptoms:
{symptoms}
"""
                    }
                ],
                temperature=0.2,
                max_tokens=200,
                top_p=1,
            )
            
            # Parse response
            response_text = completion.choices[0].message.content.strip()
            
            # Extract category and reason
            category, reason = _parse_groq_response(response_text)
            
            # Map to our priority levels
            priority_map = {
                'emergency': 'EMERGENCY',
                'urgent': 'HIGH',
                'routine': 'NORMAL',
            }
            priority = priority_map.get(category.lower(), 'NORMAL')
            
            return {
                'success': True,
                'category': category,
                'priority': priority,
                'reason': reason,
                'assessment': response_text,
                'pet_id': pet_id,
                'symptoms': symptoms,
                'model': GROQ_MODEL,
            }
            
        except Exception as e:
            print(f"Groq API error: {e}")
            # Fallthrough to fallback
    
    # Step 3: Fallback to keyword-based analysis
    return _fallback_symptom_analysis(symptoms)


def _parse_groq_response(response: str) -> Tuple[str, str]:
    """Parse the Groq response to extract category and reason."""
    category = "Routine"
    reason = "Unable to parse response"
    
    lines = response.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.lower().startswith('category:'):
            cat = line.split(':', 1)[1].strip()
            # Clean up the category
            if 'emergency' in cat.lower():
                category = 'Emergency'
            elif 'urgent' in cat.lower():
                category = 'Urgent'
            else:
                category = 'Routine'
        elif line.lower().startswith('reason:'):
            reason = line.split(':', 1)[1].strip()
    
    return category, reason


def _fallback_symptom_analysis(symptoms: str) -> Dict[str, Any]:
    """Fallback keyword-based analysis when Groq is unavailable."""
    from .priority_analyzer import analyze_priority
    
    priority, reason, keywords = analyze_priority(symptoms)
    
    # Map priority to category
    category_map = {
        'EMERGENCY': 'Emergency',
        'HIGH': 'Urgent',
        'NORMAL': 'Routine',
        'LOW': 'Routine',
    }
    
    return {
        'success': True,
        'category': category_map.get(priority, 'Routine'),
        'priority': priority,
        'reason': reason,
        'assessment': f"Category: {category_map.get(priority, 'Routine')}\nReason: {reason}",
        'keywords': keywords,
        'model': 'keyword-fallback',
    }


# ============================================================================
# PYTORCH SKIN DISEASE ANALYZER
# ============================================================================

def analyze_skin_image(image_path: str) -> Dict[str, Any]:
    """
    Analyze a pet skin image using PyTorch model.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dict with disease prediction and confidence
    """
    try:
        from ai_diagnosis.ai_model import analyze_skin_image as pytorch_analyze
        from ai_diagnosis.ai_model import get_treatment_info, is_model_loaded
        
        if not is_model_loaded():
            return {
                'success': False,
                'error': 'AI model not loaded',
                'disease': 'UNKNOWN',
                'confidence': 0,
            }
        
        # Run PyTorch prediction
        result = pytorch_analyze(image_path)
        
        # Get treatment info
        treatment = get_treatment_info(result['primary_disease'])
        
        return {
            'success': True,
            'disease': result['primary_disease'],
            'disease_name': result.get('primary_disease_name', result['primary_disease']),
            'confidence': result['primary_confidence'],
            'alternatives': result.get('alternatives', []),
            'treatment': treatment,
            'processing_time': result.get('processing_time', 0),
            'model_version': result.get('model_version', 'unknown'),
        }
        
    except Exception as e:
        print(f"Skin analysis error: {e}")
        return {
            'success': False,
            'error': str(e),
            'disease': 'UNKNOWN',
            'confidence': 0,
        }


# ============================================================================
# UNIFIED ASSESSMENT FUNCTION
# ============================================================================

def get_full_assessment(
    symptoms: str = None,
    image_path: str = None,
    pet_id: str = None
) -> Dict[str, Any]:
    """
    Get a full AI assessment combining both symptom analysis and image analysis.
    
    Args:
        symptoms: Text description of symptoms (optional)
        image_path: Path to skin image (optional)
        pet_id: Pet identifier (optional)
        
    Returns:
        Dict with combined assessment results
    """
    result = {
        'success': True,
        'pet_id': pet_id,
        'symptom_assessment': None,
        'image_assessment': None,
        'overall_priority': 'NORMAL',
        'requires_emergency': False,
    }
    
    # Analyze symptoms if provided
    if symptoms and symptoms.strip():
        symptom_result = analyze_symptoms_with_groq(symptoms, pet_id)
        result['symptom_assessment'] = symptom_result
        
        if symptom_result.get('priority') == 'EMERGENCY':
            result['overall_priority'] = 'EMERGENCY'
            result['requires_emergency'] = True
        elif symptom_result.get('priority') == 'HIGH' and result['overall_priority'] != 'EMERGENCY':
            result['overall_priority'] = 'HIGH'
    
    # Analyze image if provided
    if image_path and os.path.exists(image_path):
        image_result = analyze_skin_image(image_path)
        result['image_assessment'] = image_result
        
        # Check if disease warrants emergency
        if image_result.get('success'):
            disease = image_result.get('disease', '')
            confidence = image_result.get('confidence', 0)
            
            # High confidence serious diseases upgrade priority
            if disease in ['MANGE', 'RINGWORM'] and confidence > 0.8:
                if result['overall_priority'] not in ['EMERGENCY']:
                    result['overall_priority'] = 'HIGH'
    
    return result


# ============================================================================
# DJANGO VIEW HELPERS
# ============================================================================

def get_appointment_priority(reason: str, pet_id: str = None) -> Tuple[str, str, bool]:
    """
    Analyze appointment reason and return priority information.
    
    Args:
        reason: The appointment reason/symptoms text
        pet_id: Optional pet ID
        
    Returns:
        Tuple of (priority_level, reason_text, is_emergency)
    """
    result = analyze_symptoms_with_groq(reason, pet_id)
    
    priority = result.get('priority', 'NORMAL')
    reason_text = result.get('reason', 'Standard appointment')
    is_emergency = priority == 'EMERGENCY'
    
    return priority, reason_text, is_emergency


def save_assessment_to_json(assessment: Dict, output_path: str = None) -> str:
    """
    Save assessment result to JSON file.
    
    Args:
        assessment: The assessment dictionary
        output_path: Optional output path (defaults to media/assessments/)
        
    Returns:
        Path to saved file
    """
    if output_path is None:
        assessments_dir = os.path.join(settings.MEDIA_ROOT, 'assessments')
        os.makedirs(assessments_dir, exist_ok=True)
        
        import time
        filename = f"assessment_{int(time.time())}.json"
        output_path = os.path.join(assessments_dir, filename)
    
    with open(output_path, 'w') as f:
        json.dump(assessment, f, indent=4)
    
    return output_path


# ============================================================================
# API RESPONSE FORMATTERS
# ============================================================================

def format_symptom_response(assessment: Dict) -> Dict:
    """Format symptom assessment for API response."""
    return {
        'status': 'success' if assessment.get('success') else 'error',
        'priority': assessment.get('priority', 'NORMAL'),
        'category': assessment.get('category', 'Routine'),
        'reason': assessment.get('reason', ''),
        'full_assessment': assessment.get('assessment', ''),
        'model_used': assessment.get('model', 'unknown'),
    }


def format_image_response(assessment: Dict) -> Dict:
    """Format image assessment for API response."""
    if not assessment.get('success'):
        return {
            'status': 'error',
            'error': assessment.get('error', 'Unknown error'),
        }
    
    return {
        'status': 'success',
        'disease': assessment.get('disease'),
        'disease_name': assessment.get('disease_name'),
        'confidence': f"{assessment.get('confidence', 0):.2%}",
        'confidence_raw': assessment.get('confidence', 0),
        'alternatives': [
            {
                'disease': alt.get('disease'),
                'confidence': f"{alt.get('confidence', 0):.2%}",
            }
            for alt in assessment.get('alternatives', [])
        ],
        'treatment': assessment.get('treatment', {}),
        'model_version': assessment.get('model_version'),
    }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("AI Bridge Test")
    print("=" * 60)
    
    # Test symptom analysis
    test_symptoms = [
        "My dog is not breathing and has blue gums",
        "Cat has been vomiting for 2 hours",
        "Annual vaccination checkup",
        "Dog scratching a lot, some hair loss",
    ]
    
    print("\n--- Symptom Analysis Tests ---\n")
    for symptoms in test_symptoms:
        result = analyze_symptoms_with_groq(symptoms)
        print(f"Symptoms: {symptoms[:50]}...")
        print(f"  Priority: {result.get('priority')}")
        print(f"  Category: {result.get('category')}")
        print(f"  Reason: {result.get('reason')}")
        print()
