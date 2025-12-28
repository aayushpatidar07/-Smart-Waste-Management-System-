"""
============================================
Smart Waste Management System
AI/ML Module - Waste Level Predictor
============================================
Predicts which bins need collection based on:
- Current waste level
- Historical fill rate
- Time since last collection
Uses scikit-learn for ML predictions
============================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Bin, Database
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression


class WasteLevelPredictor:
    """
    AI-based waste level predictor
    Predicts future waste levels and identifies bins needing collection
    """
    
    def __init__(self):
        self.bin_model = Bin()
        self.db = Database()
    
    def get_fill_rate(self, bin_id):
        """
        Calculate average fill rate for a bin
        Returns: percentage increase per hour
        """
        # Get sensor logs from last 7 days
        query = """
            SELECT waste_level, timestamp
            FROM sensor_logs
            WHERE bin_id = %s
            AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            ORDER BY timestamp ASC
        """
        logs = self.db.execute_query(query, (bin_id,))
        
        if not logs or len(logs) < 2:
            # No sufficient data, use default fill rate
            return 2.0  # 2% per hour default
        
        # Calculate fill rate using linear regression
        try:
            timestamps = []
            levels = []
            
            base_time = logs[0]['timestamp']
            
            for log in logs:
                # Convert timestamp to hours since first log
                time_diff = (log['timestamp'] - base_time).total_seconds() / 3600
                timestamps.append(time_diff)
                levels.append(float(log['waste_level']))
            
            # Reshape for sklearn
            X = np.array(timestamps).reshape(-1, 1)
            y = np.array(levels)
            
            # Linear regression
            model = LinearRegression()
            model.fit(X, y)
            
            # Fill rate is the slope (coefficient)
            fill_rate = model.coef_[0]
            
            # Ensure fill rate is positive and reasonable
            if fill_rate <= 0:
                return 2.0
            if fill_rate > 10:  # Cap at 10% per hour
                return 10.0
            
            return fill_rate
            
        except Exception as e:
            print(f"Error calculating fill rate for bin {bin_id}: {e}")
            return 2.0
    
    def predict_time_to_full(self, bin_id, current_level, fill_rate):
        """
        Predict hours until bin reaches 100%
        Args:
            bin_id: Bin ID
            current_level: Current waste level (%)
            fill_rate: Fill rate (% per hour)
        Returns: Hours until full
        """
        if current_level >= 100:
            return 0
        
        if fill_rate <= 0:
            fill_rate = 2.0
        
        remaining_capacity = 100 - current_level
        hours_to_full = remaining_capacity / fill_rate
        
        return hours_to_full
    
    def predict_bins_needing_collection(self, threshold_hours=24):
        """
        Predict which bins will need collection within threshold hours
        Args:
            threshold_hours: Look-ahead time window (default 24 hours)
        Returns: List of bins with predictions
        """
        # Get all active bins
        all_bins = self.bin_model.get_all_bins()
        
        predictions = []
        
        for bin_data in all_bins:
            if bin_data['status'] != 'active':
                continue
            
            bin_id = bin_data['bin_id']
            current_level = float(bin_data['waste_level'])
            
            # Calculate fill rate
            fill_rate = self.get_fill_rate(bin_id)
            
            # Predict time to full
            hours_to_full = self.predict_time_to_full(bin_id, current_level, fill_rate)
            
            # Predict level after threshold hours
            predicted_level = current_level + (fill_rate * threshold_hours)
            if predicted_level > 100:
                predicted_level = 100
            
            # Priority calculation
            priority = 'low'
            if current_level >= 90:
                priority = 'critical'
            elif current_level >= 80:
                priority = 'high'
            elif hours_to_full <= threshold_hours:
                priority = 'medium'
            
            # Add to predictions if needs attention
            if current_level >= 70 or hours_to_full <= threshold_hours:
                predictions.append({
                    'bin_id': bin_id,
                    'bin_code': bin_data['bin_code'],
                    'location': bin_data['location'],
                    'zone': bin_data['zone'],
                    'current_level': round(current_level, 2),
                    'fill_rate': round(fill_rate, 2),
                    'hours_to_full': round(hours_to_full, 1),
                    'predicted_level_24h': round(predicted_level, 2),
                    'priority': priority,
                    'needs_collection': hours_to_full <= threshold_hours or current_level >= 80,
                    'latitude': float(bin_data['latitude']) if bin_data['latitude'] else None,
                    'longitude': float(bin_data['longitude']) if bin_data['longitude'] else None
                })
        
        # Sort by priority and current level
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        predictions.sort(key=lambda x: (priority_order[x['priority']], -x['current_level']))
        
        return predictions
    
    def get_optimal_collection_bins(self, max_bins=10):
        """
        Get optimal set of bins for today's collection
        Args:
            max_bins: Maximum number of bins in route
        Returns: List of bin IDs to collect
        """
        predictions = self.predict_bins_needing_collection(threshold_hours=24)
        
        # Filter bins that need collection
        bins_to_collect = [p for p in predictions if p['needs_collection']]
        
        # Limit to max_bins
        bins_to_collect = bins_to_collect[:max_bins]
        
        return bins_to_collect


# =============================================
# TESTING FUNCTION
# =============================================

def test_predictor():
    """Test the waste level predictor"""
    print("=" * 60)
    print("AI Waste Level Predictor - Test Results")
    print("=" * 60)
    
    predictor = WasteLevelPredictor()
    
    # Get predictions for next 24 hours
    predictions = predictor.predict_bins_needing_collection(threshold_hours=24)
    
    print(f"\nFound {len(predictions)} bins requiring attention")
    print("\nBins Needing Collection (Next 24 Hours):")
    print("-" * 60)
    
    for pred in predictions[:10]:  # Show top 10
        print(f"\nBin: {pred['bin_code']} - {pred['location']}")
        print(f"  Current Level: {pred['current_level']}%")
        print(f"  Fill Rate: {pred['fill_rate']}% per hour")
        print(f"  Hours to Full: {pred['hours_to_full']} hours")
        print(f"  Predicted Level (24h): {pred['predicted_level_24h']}%")
        print(f"  Priority: {pred['priority'].upper()}")
        print(f"  Needs Collection: {'YES' if pred['needs_collection'] else 'NO'}")
    
    print("\n" + "=" * 60)
    
    # Get optimal collection set
    optimal_bins = predictor.get_optimal_collection_bins(max_bins=8)
    print(f"\nOptimal Collection Set ({len(optimal_bins)} bins):")
    print("-" * 60)
    for bin_data in optimal_bins:
        print(f"  {bin_data['bin_code']}: {bin_data['location']} ({bin_data['current_level']}%)")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_predictor()
