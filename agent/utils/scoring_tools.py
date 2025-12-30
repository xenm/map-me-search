"""
Shared scoring tools for places search
Common utilities used by both main.py and agent/agent.py
"""

from typing import Dict


def calculate_distance_score(distance_km: float) -> dict:
    """Calculates a relevance score based on distance from city center.
    
    Args:
        distance_km: Distance in kilometers from city center
        
    Returns:
        Dictionary with status and score.
        Success: {"status": "success", "score": 10}
        Error: {"status": "error", "error_message": "Invalid distance"}
    """
    if distance_km < 0:
        return {
            "status": "error",
            "error_message": "Distance cannot be negative"
        }
    
    # Closer = higher score (10 points max)
    if distance_km <= 1:
        score = 10
    elif distance_km <= 3:
        score = 8
    elif distance_km <= 5:
        score = 6
    elif distance_km <= 10:
        score = 4
    else:
        score = 2
    
    return {
        "status": "success",
        "score": score,
        "distance_km": distance_km
    }


def get_place_category_boost(category: str, preferences: str) -> dict:
    """Calculates a boost score based on how well a category matches preferences.
    
    Args:
        category: Category of the place (e.g., "restaurant", "museum")
        preferences: User's stated preferences
        
    Returns:
        Dictionary with status and boost score.
        Success: {"status": "success", "boost": 2}
        Error: {"status": "error", "error_message": "..."}
    """
    category = category.lower()
    preferences = preferences.lower()
    
    # Direct match gives highest boost
    if category in preferences or preferences in category:
        return {"status": "success", "boost": 3, "reason": "Direct match"}
    
    # Related categories get medium boost
    food_related = ["restaurant", "cafe", "coffee", "bar", "food"]
    culture_related = ["museum", "gallery", "theater", "art"]
    outdoor_related = ["park", "garden", "hiking", "beach"]
    
    if category in food_related and any(term in preferences for term in food_related):
        return {"status": "success", "boost": 2, "reason": "Food-related match"}
    if category in culture_related and any(term in preferences for term in culture_related):
        return {"status": "success", "boost": 2, "reason": "Culture-related match"}
    if category in outdoor_related and any(term in preferences for term in outdoor_related):
        return {"status": "success", "boost": 2, "reason": "Outdoor-related match"}
    
    return {"status": "success", "boost": 0, "reason": "No special match"}
