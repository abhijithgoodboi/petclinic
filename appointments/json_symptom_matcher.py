"""
JSON-based Symptom Assessment System
=====================================
Precise symptom matching against predefined emergency patterns.

Workflow:
1. User enters symptoms
2. Compare against input_symptoms.json patterns
3. If match found → Get assessment from assessment_result.json
4. Return priority based on matched case

All patterns in JSON are EMERGENCY cases with different severity levels.
"""

import json
import os
import sys
from typing import Dict, Any, Optional
from difflib import SequenceMatcher


def get_json_dir():
    if 'django' in sys.modules:
        from django.conf import settings
        return getattr(settings, 'BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JSON_DIR = get_json_dir()


def load_json_file(filename: str) -> any:
    filepath = os.path.join(JSON_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {filename}: {e}")
        return None


def normalize_text(text: str) -> str:
    """Normalize text for comparison - remove extra spaces, lowercase."""
    return ' '.join(text.lower().split())


def extract_keywords(text: str) -> set:
    """Extract individual keywords from symptom text."""
    delimiters = [',', ';', '.', ' and ', ' or ', ' with ', '-', '/', '(', ')', '  ']
    normalized = text.lower()
    for delim in delimiters:
        normalized = normalized.replace(delim, ' ')
    return set(normalized.split())


def keyword_similarity(keywords1: set, keywords2: set) -> float:
    """Calculate similarity between two keyword sets."""
    if not keywords1 or not keywords2:
        return 0.0
    intersection = keywords1 & keywords2
    union = keywords1 | keywords2
    return len(intersection) / len(union) if union else 0.0


def sequence_similarity(text1: str, text2: str) -> float:
    """Calculate sequence similarity between two texts."""
    return SequenceMatcher(None, text1, text2).ratio()


def check_exact_match(user_symptoms: str, json_symptoms: str) -> bool:
    """Check if symptoms match exactly (after normalization)."""
    return normalize_text(user_symptoms) == normalize_text(json_symptoms)


def check_partial_match(user_symptoms: str, json_symptoms: str) -> bool:
    """Check if user symptoms contain or match substantially with JSON symptoms."""
    user_norm = normalize_text(user_symptoms)
    json_norm = normalize_text(json_symptoms)
    
    # Check if JSON symptoms are contained in user symptoms
    if json_norm in user_norm:
        return True
    
    # Check if user symptoms are contained in JSON symptoms
    if user_norm in json_norm:
        return True
    
    # Check keyword overlap (at least 50% of JSON keywords must be present)
    user_keywords = extract_keywords(user_symptoms)
    json_keywords = extract_keywords(json_symptoms)
    similarity = keyword_similarity(user_keywords, json_keywords)
    
    return similarity >= 0.5


def match_symptoms(symptoms: str, pet_id: str = None) -> Dict[str, Any]:
    """
    Match user symptoms against JSON patterns.
    
    Returns:
        Dict with:
            - matched: bool - Whether a match was found
            - priority: str - EMERGENCY/HIGH/NORMAL/LOW
            - severity: str - CRITICAL/SEVERE/MODERATE (from JSON)
            - assessment: str - Full assessment text
            - reason: str - Reason for priority
            - pet_id: str - Pet ID from matched JSON
            - symptoms_matched: str - The JSON symptoms that matched
            - match_score: float - How close the match was
    """
    if not symptoms or not symptoms.strip():
        return {
            'matched': False,
            'priority': 'NORMAL',
            'severity': None,
            'reason': 'No symptoms provided',
            'source': 'json_matcher'
        }
    
    user_symptoms = symptoms.strip()
    
    # Load JSON databases
    symptom_data = load_json_file('input_symptoms.json')
    assessment_data = load_json_file('assessment_result.json')
    
    if symptom_data is None or assessment_data is None:
        return {
            'matched': False,
            'priority': 'NORMAL',
            'reason': 'Symptom database not available',
            'source': 'json_matcher'
        }
    
    # Convert to dict if it's a list
    if isinstance(symptom_data, list):
        symptom_entries = symptom_data
    else:
        symptom_entries = [symptom_data]
    
    best_match = None
    best_match_score = 0
    match_type = None  # 'exact', 'partial'
    
    for entry in symptom_entries:
        entry_symptoms = entry.get('symptoms', '')
        entry_pet_id = entry.get('pet_id', '')
        
        # Filter by pet_id if provided
        if pet_id and entry_pet_id and entry_pet_id != pet_id:
            continue
        
        # Try exact match first
        if check_exact_match(user_symptoms, entry_symptoms):
            best_match = entry
            best_match_score = 1.0
            match_type = 'exact'
            break
        
        # Try partial match
        if check_partial_match(user_symptoms, entry_symptoms):
            # Calculate match score
            seq_score = sequence_similarity(
                normalize_text(user_symptoms),
                normalize_text(entry_symptoms)
            )
            keyword_score = keyword_similarity(
                extract_keywords(user_symptoms),
                extract_keywords(entry_symptoms)
            )
            # Use the higher score
            score = max(seq_score, keyword_score)
            
            if score > best_match_score:
                best_match = entry
                best_match_score = score
                match_type = 'partial'
    
    if best_match:
        entry_symptoms = best_match.get('symptoms', '')
        entry_pet_id = best_match.get('pet_id', '')
        
        # Get assessment from assessment_result.json
        assessment = assessment_data.get(entry_pet_id) if isinstance(assessment_data, dict) else None
        
        if assessment:
            assessment_text = assessment.get('assessment', '')
            priority = extract_priority_from_assessment(assessment_text)
            reason = extract_reason_from_assessment(assessment_text)
            severity = extract_severity_from_assessment(assessment_text)
            
            return {
                'matched': True,
                'priority': priority,
                'severity': severity,
                'reason': reason,
                'full_assessment': assessment_text,
                'pet_id': entry_pet_id,
                'symptoms_matched': entry_symptoms,
                'match_score': best_match_score,
                'match_type': match_type,
                'source': 'json_matcher'
            }
        else:
            # Assessment not found, use default emergency
            return {
                'matched': True,
                'priority': 'EMERGENCY',
                'severity': 'MODERATE',
                'reason': 'Symptoms matched predefined emergency pattern',
                'full_assessment': '',
                'pet_id': entry_pet_id,
                'symptoms_matched': entry_symptoms,
                'match_score': best_match_score,
                'match_type': match_type,
                'source': 'json_matcher'
            }
    
    return {
        'matched': False,
        'priority': 'NORMAL',
        'severity': None,
        'reason': 'No matching emergency symptoms found',
        'source': 'json_matcher'
    }


def extract_priority_from_assessment(assessment_text: str) -> str:
    """Extract priority from assessment text."""
    text_lower = assessment_text.lower()
    if 'emergency' in text_lower:
        return 'EMERGENCY'
    elif 'urgent' in text_lower:
        return 'HIGH'
    elif 'routine' in text_lower:
        return 'NORMAL'
    return 'NORMAL'


def extract_severity_from_assessment(assessment_text: str) -> str:
    """Extract severity level from assessment text."""
    text_lower = assessment_text.lower()
    
    # All JSON patterns are emergencies, determine severity
    critical_keywords = ['respiratory arrest', 'hypoxia', 'cpr', 'cardiac', 'seizure', 
                        'poisoning', 'internal hemorrhage', 'hypothermia', 'shock',
                        'near drowning', 'electrocution', 'heat stroke']
    
    severe_keywords = ['venom', 'bloat', 'dystocia', 'trauma', 'fracture', 
                      'burns', 'pulmonary edema', 'wound care']
    
    for kw in critical_keywords:
        if kw in text_lower:
            return 'CRITICAL'
    
    for kw in severe_keywords:
        if kw in text_lower:
            return 'SEVERE'
    
    return 'MODERATE'


def extract_reason_from_assessment(assessment_text: str) -> str:
    """Extract reason from assessment text."""
    if 'reason:' in assessment_text.lower():
        parts = assessment_text.lower().split('reason:')
        if len(parts) > 1:
            reason = parts[-1].strip()
            return reason[0].upper() + reason[1:] if reason else 'Symptoms require attention'
    
    if assessment_text:
        first_sentence = assessment_text.split('.')[0]
        return first_sentence.strip()
    return 'Symptoms require attention'


def is_emergency_symptom(symptoms: str) -> bool:
    """Quick check if symptoms are in the emergency database."""
    result = match_symptoms(symptoms)
    return result['matched'] and result['priority'] == 'EMERGENCY'


def get_severity_level(symptoms: str) -> Optional[str]:
    """Get severity level for symptoms."""
    result = match_symptoms(symptoms)
    return result.get('severity')


def get_emergency_info(symptoms: str) -> Dict[str, Any]:
    """Get complete emergency info for symptoms."""
    return match_symptoms(symptoms)


if __name__ == '__main__':
    print("=" * 80)
    print("JSON Symptom Matcher - Precise Matching Test")
    print("=" * 80)
    
    # Test cases - exact matches
    exact_tests = [
        "Vomiting, not eating for two days, very weak, pale gums",
        "Not breathing, blue gums, unconscious",
        "Hit by car, severe bleeding, can't move legs",
        "Snake bite, swelling rapidly, difficulty breathing",
        "Seizures lasting more than 5 minutes, collapsed",
    ]
    
    # Test cases - variations
    variation_tests = [
        ("My dog is vomiting and not eating", "Vomiting, not eating for two days, very weak, pale gums"),
        ("Cat was hit by car", "Hit by car, severe bleeding, can't move legs"),
        ("Dog having seizures, collapsed", "Seizures lasting more than 5 minutes, collapsed"),
        ("Regular checkup", "Vomiting, not eating for two days, very weak, pale gums"),
        ("Mild scratching", "Vomiting, not eating for two days, very weak, pale gums"),
    ]
    
    print("\n--- Exact Match Tests ---")
    for symptoms in exact_tests:
        result = match_symptoms(symptoms)
        print(f"\nInput: {symptoms}")
        print(f"  Matched: {result['matched']}")
        print(f"  Priority: {result['priority']}")
        print(f"  Severity: {result.get('severity', 'N/A')}")
        print(f"  Match Score: {result.get('match_score', 0):.2%}")
        print(f"  Pet ID: {result.get('pet_id', 'N/A')}")
    
    print("\n--- Variation Match Tests ---")
    for user_input, json_pattern in variation_tests:
        result = match_symptoms(user_input)
        print(f"\nUser Input: {user_input}")
        print(f"  JSON Pattern: {json_pattern}")
        print(f"  Matched: {result['matched']}")
        print(f"  Priority: {result['priority']}")
        print(f"  Severity: {result.get('severity', 'N/A')}")
        print(f"  Match Score: {result.get('match_score', 0):.2%}")
        print(f"  Match Type: {result.get('match_type', 'N/A')}")
