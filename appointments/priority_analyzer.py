"""
Priority Analyzer for Appointment Descriptions
Analyzes the reason/description text and determines appropriate priority level.

This file can be easily customized to add/remove keywords or adjust priority rules.
"""

import re
from typing import Tuple

# ============================================================================
# PRIORITY KEYWORDS CONFIGURATION
# Edit these lists to customize priority detection
# ============================================================================

# EMERGENCY - Requires immediate attention (life-threatening situations)
EMERGENCY_KEYWORDS = [
    # Breathing issues
    'not breathing', 'cant breathe', "can't breathe", 'difficulty breathing',
    'choking', 'suffocating', 'gasping', 'blue gums', 'blue tongue',
    
    # Bleeding/Trauma
    'severe bleeding', 'heavy bleeding', 'profuse bleeding', 'blood loss',
    'hit by car', 'accident', 'trauma', 'broken bone', 'fracture',
    'deep wound', 'puncture wound', 'attacked by',
    
    # Poisoning
    'poisoned', 'poison', 'toxic', 'ate poison', 'rat poison',
    'antifreeze', 'chocolate poisoning', 'xylitol',
    
    # Seizures/Collapse
    'seizure', 'convulsion', 'collapse', 'collapsed', 'unconscious',
    'unresponsive', 'not moving', 'paralyzed', 'cant walk', "can't walk",
    
    # Severe conditions
    'bloat', 'twisted stomach', 'gastric torsion', 'heatstroke',
    'heat stroke', 'drowning', 'electrocution', 'snake bite', 'bee sting allergy',
    
    # Birth emergencies
    'difficult labor', 'dystocia', 'stuck puppy', 'stuck kitten',
    'prolonged labor', 'birthing emergency',
    
    # Animal attacks/bites
    'snake bite', 'snakebite', 'snake bit', 'bitten by snake',
    'spider bite', 'scorpion sting', 'venomous',
]

# HIGH PRIORITY - Urgent but not immediately life-threatening
HIGH_PRIORITY_KEYWORDS = [
    # Pain indicators
    'severe pain', 'extreme pain', 'screaming', 'crying in pain',
    'cant stand', "can't stand", 'limping badly', 'unable to walk',
    
    # Vomiting/Diarrhea
    'vomiting blood', 'blood in vomit', 'bloody diarrhea',
    'continuous vomiting', 'cant keep food down', "can't keep food down",
    'vomiting for hours', 'severe vomiting', 'projectile vomiting',
    
    # Eye emergencies
    'eye injury', 'eye popped', 'proptosis', 'scratched eye',
    'eye swollen shut', 'sudden blindness',
    
    # Urinary issues
    'cant urinate', "can't urinate", 'blocked', 'straining to pee',
    'no urine', 'bloody urine', 'urinary blockage',
    
    # Allergic reactions
    'swollen face', 'hives', 'allergic reaction', 'face swelling',
    'throat swelling', 'anaphylaxis',
    
    # Infections
    'high fever', 'very hot', 'severe infection', 'abscess burst',
    'pus', 'infected wound', 'septic',
    
    # Eating issues
    'not eating for days', 'refuses food', 'wont eat for 2 days',
    'hasnt eaten', "hasn't eaten", 'anorexia',
]

# NORMAL PRIORITY - Standard appointments (default)
NORMAL_PRIORITY_KEYWORDS = [
    # Routine care
    'checkup', 'check-up', 'check up', 'vaccination', 'vaccine',
    'annual exam', 'wellness', 'routine', 'regular visit',
    'booster', 'shots', 'immunization',
    
    # Minor issues
    'mild', 'slight', 'minor', 'small', 'little',
    'occasional', 'sometimes', 'started recently',
    
    # Grooming related
    'nail trim', 'ear cleaning', 'dental cleaning',
    'grooming', 'bath', 'matted fur',
]

# LOW PRIORITY - Non-urgent, can wait
LOW_PRIORITY_KEYWORDS = [
    # Cosmetic/Optional
    'microchip', 'microchipping', 'health certificate',
    'travel certificate', 'spay', 'neuter', 'elective surgery',
    
    # Follow-ups
    'follow up', 'follow-up', 'recheck', 're-check',
    'medication refill', 'refill', 'prescription renewal',
    
    # Behavioral (non-urgent)
    'behavioral consultation', 'training advice',
    'diet advice', 'nutrition consultation',
]


# ============================================================================
# SYMPTOM SEVERITY PATTERNS
# More complex patterns that indicate severity
# ============================================================================

SEVERITY_PATTERNS = {
    'EMERGENCY': [
        r'not (breathing|moving|responding)',
        r'(severe|heavy|profuse) bleeding',
        r'(hit|struck) by (car|vehicle)',
        r'(seizure|convulsion)s? (for|lasting)',
        r'(collapse|passed out|unconscious)',
    ],
    'HIGH': [
        r'vomiting (blood|for \d+ hours?)',
        r'(bloody|blood in) (stool|diarrhea|urine)',
        r"(can't|cannot|unable to) (walk|stand|eat|urinate)",
        r'swollen (face|eye|throat)',
        r'(severe|extreme|intense) pain',
        r'not eating for (\d+) days?',
    ],
    'NORMAL': [
        r'(annual|routine|regular) (checkup|exam|visit)',
        r'(vaccination|vaccine|booster)',
        r'(mild|slight|minor|occasional)',
    ],
}


def analyze_priority(description: str) -> Tuple[str, str, list]:
    """
    Analyze appointment description and determine priority level.
    
    Args:
        description: The reason/description text from appointment booking
        
    Returns:
        Tuple of (priority_level, reason, matched_keywords)
        - priority_level: 'LOW', 'NORMAL', 'HIGH', or 'EMERGENCY'
        - reason: Human-readable explanation for the priority
        - matched_keywords: List of keywords that triggered this priority
    """
    if not description:
        return 'NORMAL', 'No description provided', []
    
    # Normalize text for matching
    text = description.lower().strip()
    matched_keywords = []
    
    # Check for EMERGENCY keywords first (highest priority)
    for keyword in EMERGENCY_KEYWORDS:
        if keyword.lower() in text:
            matched_keywords.append(keyword)
    
    if matched_keywords:
        return 'EMERGENCY', f'Emergency symptoms detected: {", ".join(matched_keywords[:3])}', matched_keywords
    
    # Check regex patterns for EMERGENCY
    for pattern in SEVERITY_PATTERNS.get('EMERGENCY', []):
        if re.search(pattern, text, re.IGNORECASE):
            return 'EMERGENCY', f'Emergency pattern detected', [pattern]
    
    # Check for HIGH priority keywords
    matched_keywords = []
    for keyword in HIGH_PRIORITY_KEYWORDS:
        if keyword.lower() in text:
            matched_keywords.append(keyword)
    
    if matched_keywords:
        return 'HIGH', f'Urgent symptoms detected: {", ".join(matched_keywords[:3])}', matched_keywords
    
    # Check regex patterns for HIGH
    for pattern in SEVERITY_PATTERNS.get('HIGH', []):
        if re.search(pattern, text, re.IGNORECASE):
            return 'HIGH', f'Urgent pattern detected', [pattern]
    
    # Check for LOW priority keywords
    matched_keywords = []
    for keyword in LOW_PRIORITY_KEYWORDS:
        if keyword.lower() in text:
            matched_keywords.append(keyword)
    
    if matched_keywords:
        return 'LOW', f'Routine/follow-up visit: {", ".join(matched_keywords[:3])}', matched_keywords
    
    # Check for NORMAL priority keywords (explicit routine care)
    matched_keywords = []
    for keyword in NORMAL_PRIORITY_KEYWORDS:
        if keyword.lower() in text:
            matched_keywords.append(keyword)
    
    if matched_keywords:
        return 'NORMAL', f'Standard appointment: {", ".join(matched_keywords[:3])}', matched_keywords
    
    # Default to NORMAL if no specific keywords found
    return 'NORMAL', 'Standard priority - no urgent keywords detected', []


def get_priority_badge_class(priority: str) -> str:
    """Get Bootstrap badge class for priority level"""
    classes = {
        'LOW': 'bg-secondary',
        'NORMAL': 'bg-primary',
        'HIGH': 'bg-warning text-dark',
        'EMERGENCY': 'bg-danger',
    }
    return classes.get(priority, 'bg-primary')


def get_priority_icon(priority: str) -> str:
    """Get Bootstrap icon for priority level"""
    icons = {
        'LOW': 'bi-arrow-down-circle',
        'NORMAL': 'bi-dash-circle',
        'HIGH': 'bi-exclamation-triangle',
        'EMERGENCY': 'bi-exclamation-octagon-fill',
    }
    return icons.get(priority, 'bi-dash-circle')


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    # Test cases
    test_descriptions = [
        "My cat is not breathing properly and has blue gums",
        "Dog was hit by a car, severe bleeding from leg",
        "Cat has been vomiting blood for 2 hours",
        "Puppy has bloody diarrhea and won't eat",
        "Annual vaccination and checkup",
        "Need to get microchip for travel",
        "Follow up visit for medication",
        "My dog has been scratching a lot lately",
        "Cat is limping slightly after jumping",
        "Snake bit my dog, swelling rapidly",
    ]
    
    print("Priority Analysis Test Results:")
    print("=" * 60)
    
    for desc in test_descriptions:
        priority, reason, keywords = analyze_priority(desc)
        print(f"\nDescription: {desc[:50]}...")
        print(f"  Priority: {priority}")
        print(f"  Reason: {reason}")
        if keywords:
            print(f"  Keywords: {keywords[:3]}")
