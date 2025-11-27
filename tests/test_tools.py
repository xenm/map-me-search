"""
Unit tests for custom tools (Day 4b)

Tests the scoring functions used in the FilterAgent.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import calculate_distance_score, get_place_category_boost


class TestDistanceScoreCalculation:
    """Test suite for calculate_distance_score function"""
    
    def test_very_close_distance(self):
        """Test score for very close distance (<=1 km)"""
        result = calculate_distance_score(0.5)
        assert result["status"] == "success"
        assert result["score"] == 10
        assert result["distance_km"] == 0.5
    
    def test_close_distance(self):
        """Test score for close distance (<=3 km)"""
        result = calculate_distance_score(2.5)
        assert result["status"] == "success"
        assert result["score"] == 8
    
    def test_medium_distance(self):
        """Test score for medium distance (<=5 km)"""
        result = calculate_distance_score(4.5)
        assert result["status"] == "success"
        assert result["score"] == 6
    
    def test_far_distance(self):
        """Test score for far distance (<=10 km)"""
        result = calculate_distance_score(8.0)
        assert result["status"] == "success"
        assert result["score"] == 4
    
    def test_very_far_distance(self):
        """Test score for very far distance (>10 km)"""
        result = calculate_distance_score(15.0)
        assert result["status"] == "success"
        assert result["score"] == 2
    
    def test_negative_distance(self):
        """Test error handling for negative distance"""
        result = calculate_distance_score(-5.0)
        assert result["status"] == "error"
        assert "error_message" in result
        assert "negative" in result["error_message"].lower()
    
    def test_zero_distance(self):
        """Test score for zero distance"""
        result = calculate_distance_score(0)
        assert result["status"] == "success"
        assert result["score"] == 10


class TestCategoryBoostCalculation:
    """Test suite for get_place_category_boost function"""
    
    def test_direct_match(self):
        """Test boost for direct category match"""
        result = get_place_category_boost("restaurant", "restaurant")
        assert result["status"] == "success"
        assert result["boost"] == 3
        assert result["reason"] == "Direct match"
    
    def test_partial_match(self):
        """Test boost for partial category match"""
        result = get_place_category_boost("cafe", "coffee cafe bar")
        assert result["status"] == "success"
        assert result["boost"] == 3
        assert result["reason"] == "Direct match"
    
    def test_food_related_match(self):
        """Test boost for food-related category match"""
        result = get_place_category_boost("restaurant", "food and dining")
        assert result["status"] == "success"
        assert result["boost"] == 2
        assert result["reason"] == "Food-related match"
    
    def test_culture_related_match(self):
        """Test boost for culture-related category match"""
        result = get_place_category_boost("museum", "art and culture")
        assert result["status"] == "success"
        assert result["boost"] == 2
        assert result["reason"] == "Culture-related match"
    
    def test_outdoor_related_match(self):
        """Test boost for outdoor-related category match"""
        result = get_place_category_boost("park", "outdoor activities")
        assert result["status"] == "success"
        assert result["boost"] == 2
        assert result["reason"] == "Outdoor-related match"
    
    def test_no_match(self):
        """Test boost for no category match"""
        result = get_place_category_boost("shopping", "museums")
        assert result["status"] == "success"
        assert result["boost"] == 0
        assert result["reason"] == "No special match"
    
    def test_case_insensitive(self):
        """Test that matching is case-insensitive"""
        result = get_place_category_boost("RESTAURANT", "restaurant")
        assert result["status"] == "success"
        assert result["boost"] == 3
        assert result["reason"] == "Direct match"


if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    pytest.main([__file__, "-v"])
