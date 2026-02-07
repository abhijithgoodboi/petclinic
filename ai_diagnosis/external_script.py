"""
External Script Handler for AI Image Analysis
This module handles triggering external scripts for image processing
and parsing their results.
"""

import os
import json
import subprocess
import tempfile
from django.conf import settings


# Define which diseases are considered emergencies
EMERGENCY_DISEASES = {
    'MANGE': {
        'severity': 'HIGH',
        'auto_emergency': True,
        'min_confidence': 0.7,
        'description': 'Mange can spread rapidly and cause severe discomfort'
    },
    'HOT_SPOT': {
        'severity': 'HIGH', 
        'auto_emergency': True,
        'min_confidence': 0.75,
        'description': 'Hot spots can worsen quickly and may indicate underlying issues'
    },
    'BACTERIAL': {
        'severity': 'MEDIUM',
        'auto_emergency': True,
        'min_confidence': 0.8,
        'description': 'Bacterial infections require prompt treatment'
    },
    'RINGWORM': {
        'severity': 'MEDIUM',
        'auto_emergency': False,
        'min_confidence': 0.7,
        'description': 'Ringworm is contagious and needs treatment'
    },
    'FUNGAL': {
        'severity': 'MEDIUM',
        'auto_emergency': False,
        'min_confidence': 0.7,
        'description': 'Fungal infections need antifungal treatment'
    },
    'DERMATITIS': {
        'severity': 'LOW',
        'auto_emergency': False,
        'min_confidence': 0.6,
        'description': 'Dermatitis needs monitoring and treatment'
    },
    'ALLERGY': {
        'severity': 'LOW',
        'auto_emergency': False,
        'min_confidence': 0.6,
        'description': 'Allergic reactions may need antihistamines'
    },
    'FLEA': {
        'severity': 'LOW',
        'auto_emergency': False,
        'min_confidence': 0.6,
        'description': 'Flea infestation needs treatment'
    },
    'ECZEMA': {
        'severity': 'LOW',
        'auto_emergency': False,
        'min_confidence': 0.6,
        'description': 'Eczema requires ongoing management'
    },
    'HEALTHY': {
        'severity': 'NONE',
        'auto_emergency': False,
        'min_confidence': 0.5,
        'description': 'No disease detected'
    },
}


def get_external_script_path():
    """Get the path to the external analysis script"""
    # Check for custom script path in settings
    script_path = getattr(settings, 'AI_EXTERNAL_SCRIPT_PATH', None)
    
    if script_path and os.path.exists(script_path):
        return script_path
    
    # Default to script in ai_diagnosis directory
    default_path = os.path.join(
        settings.BASE_DIR, 
        'ai_diagnosis', 
        'scripts', 
        'analyze_image.py'
    )
    
    return default_path if os.path.exists(default_path) else None


def run_external_script(image_path, timeout=60):
    """
    Run external script to analyze image
    
    Args:
        image_path: Path to the uploaded image
        timeout: Maximum time to wait for script (seconds)
    
    Returns:
        dict: Analysis result from script or None if failed
    """
    script_path = get_external_script_path()
    
    if not script_path:
        print("External script not found, using internal AI model")
        return None
    
    try:
        # Run the external script
        result = subprocess.run(
            ['python', script_path, image_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(script_path)
        )
        
        if result.returncode != 0:
            print(f"External script error: {result.stderr}")
            return None
        
        # Parse JSON output from script
        output = result.stdout.strip()
        if output:
            return json.loads(output)
        
        return None
        
    except subprocess.TimeoutExpired:
        print(f"External script timed out after {timeout} seconds")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse script output as JSON: {e}")
        return None
    except Exception as e:
        print(f"Error running external script: {e}")
        return None


def should_create_emergency(disease, confidence):
    """
    Determine if an emergency case should be created based on disease and confidence
    
    Args:
        disease: The predicted disease name
        confidence: Confidence score (0-1)
    
    Returns:
        tuple: (should_create: bool, severity: str, reason: str)
    """
    disease_info = EMERGENCY_DISEASES.get(disease, {})
    
    if not disease_info:
        return False, 'LOW', 'Unknown disease'
    
    min_confidence = disease_info.get('min_confidence', 0.7)
    auto_emergency = disease_info.get('auto_emergency', False)
    severity = disease_info.get('severity', 'LOW')
    description = disease_info.get('description', '')
    
    # Check if this disease + confidence warrants an emergency
    if auto_emergency and confidence >= min_confidence:
        return True, severity, description
    
    # High confidence on any non-healthy disease should flag for review
    if disease != 'HEALTHY' and confidence >= 0.9:
        return True, 'MEDIUM', f'High confidence ({confidence:.0%}) detection of {disease}'
    
    return False, severity, description


def get_urgency_level(disease, confidence):
    """
    Determine urgency level based on disease and confidence
    
    Returns one of: ROUTINE, SOON, URGENT, EMERGENCY
    """
    disease_info = EMERGENCY_DISEASES.get(disease, {})
    severity = disease_info.get('severity', 'LOW')
    
    if disease == 'HEALTHY':
        return 'ROUTINE'
    
    if severity == 'HIGH' and confidence >= 0.8:
        return 'EMERGENCY'
    elif severity == 'HIGH' and confidence >= 0.6:
        return 'URGENT'
    elif severity == 'MEDIUM' and confidence >= 0.7:
        return 'URGENT'
    elif severity == 'MEDIUM' and confidence >= 0.5:
        return 'SOON'
    elif confidence >= 0.6:
        return 'SOON'
    else:
        return 'ROUTINE'
