"""
Utilities module for map-me-search
Contains shared tools and functions used across the application
"""

from importlib import import_module

from .scoring_tools import calculate_distance_score, get_place_category_boost

__all__ = ['calculate_distance_score', 'get_place_category_boost', 'places_agent_core']

def __getattr__(name: str):
    if name == 'places_agent_core':
        return import_module('.places_agent_core', __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
