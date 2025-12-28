"""
============================================
Smart Waste Management System
AI Module - Route Optimizer
============================================
Optimizes waste collection routes using:
- Nearest neighbor algorithm
- Priority-based scheduling
- Distance calculations
============================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Bin, Database
import math


class RouteOptimizer:
    """
    Route optimization for waste collection
    Uses nearest neighbor algorithm with priority weighting
    """
    
    def __init__(self):
        self.bin_model = Bin()
        self.db = Database()
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate distance between two coordinates using Haversine formula
        Returns: Distance in kilometers
        """
        # Radius of Earth in km
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return distance
    
    def get_bin_priority_score(self, waste_level):
        """
        Calculate priority score based on waste level
        Higher score = higher priority
        """
        if waste_level >= 90:
            return 100
        elif waste_level >= 80:
            return 80
        elif waste_level >= 70:
            return 60
        elif waste_level >= 60:
            return 40
        else:
            return 20
    
    def optimize_route(self, bin_ids, start_location=None):
        """
        Optimize route using nearest neighbor with priority weighting
        Args:
            bin_ids: List of bin IDs to include in route
            start_location: Starting point (lat, lon) - optional
        Returns: Optimized route with bins in order
        """
        if not bin_ids:
            return {
                'bins': [],
                'total_distance': 0,
                'optimization_method': 'nearest_neighbor'
            }
        
        # Get bin details
        bins = []
        for bin_id in bin_ids:
            bin_data = self.bin_model.get_bin_by_id(bin_id)
            if bin_data and bin_data['latitude'] and bin_data['longitude']:
                bins.append({
                    'bin_id': bin_data['bin_id'],
                    'bin_code': bin_data['bin_code'],
                    'location': bin_data['location'],
                    'latitude': float(bin_data['latitude']),
                    'longitude': float(bin_data['longitude']),
                    'waste_level': float(bin_data['waste_level']),
                    'priority_score': self.get_bin_priority_score(float(bin_data['waste_level']))
                })
        
        if not bins:
            return {
                'bins': [],
                'total_distance': 0,
                'optimization_method': 'nearest_neighbor'
            }
        
        # Starting point (use first bin if not specified)
        if start_location:
            current_lat, current_lon = start_location
        else:
            # Sort by priority and use highest priority bin as start
            bins.sort(key=lambda x: x['priority_score'], reverse=True)
            current_lat = bins[0]['latitude']
            current_lon = bins[0]['longitude']
        
        # Nearest neighbor with priority weighting
        optimized_route = []
        remaining_bins = bins.copy()
        total_distance = 0
        
        while remaining_bins:
            # Calculate weighted score for each remaining bin
            # Score = priority_score - (distance * distance_weight)
            distance_weight = 5  # Adjust this to balance priority vs distance
            
            best_bin = None
            best_score = -float('inf')
            
            for bin_data in remaining_bins:
                distance = self.calculate_distance(
                    current_lat, current_lon,
                    bin_data['latitude'], bin_data['longitude']
                )
                
                # Weighted score: higher priority and lower distance is better
                score = bin_data['priority_score'] - (distance * distance_weight)
                
                if score > best_score:
                    best_score = score
                    best_bin = bin_data
                    best_distance = distance
            
            # Add best bin to route
            if best_bin:
                optimized_route.append({
                    'sequence': len(optimized_route) + 1,
                    'bin_id': best_bin['bin_id'],
                    'bin_code': best_bin['bin_code'],
                    'location': best_bin['location'],
                    'latitude': best_bin['latitude'],
                    'longitude': best_bin['longitude'],
                    'waste_level': best_bin['waste_level'],
                    'distance_from_previous': round(best_distance, 2)
                })
                
                total_distance += best_distance
                current_lat = best_bin['latitude']
                current_lon = best_bin['longitude']
                remaining_bins.remove(best_bin)
        
        return {
            'bins': optimized_route,
            'total_bins': len(optimized_route),
            'total_distance': round(total_distance, 2),
            'optimization_method': 'nearest_neighbor_priority_weighted',
            'average_waste_level': round(sum(b['waste_level'] for b in optimized_route) / len(optimized_route), 2) if optimized_route else 0
        }
    
    def optimize_route_by_zone(self, zone, max_bins=10):
        """
        Create optimized route for a specific zone
        Args:
            zone: Zone name
            max_bins: Maximum bins in route
        Returns: Optimized route
        """
        # Get all bins in zone that need collection (>= 60%)
        query = """
            SELECT bin_id, bin_code, location, latitude, longitude, waste_level
            FROM bins
            WHERE zone = %s AND status = 'active' AND waste_level >= 60
            ORDER BY waste_level DESC
            LIMIT %s
        """
        bins = self.db.execute_query(query, (zone, max_bins))
        
        if not bins:
            return {
                'bins': [],
                'total_distance': 0,
                'zone': zone
            }
        
        bin_ids = [b['bin_id'] for b in bins]
        route = self.optimize_route(bin_ids)
        route['zone'] = zone
        
        return route
    
    def create_daily_routes(self, zones=None, bins_per_route=8):
        """
        Create optimized routes for all zones
        Args:
            zones: List of zones (None = all zones)
            bins_per_route: Max bins per route
        Returns: List of routes for each zone
        """
        if zones is None:
            # Get all zones
            query = "SELECT DISTINCT zone FROM bins WHERE status = 'active' ORDER BY zone"
            zone_result = self.db.execute_query(query)
            zones = [z['zone'] for z in zone_result] if zone_result else []
        
        daily_routes = []
        
        for zone in zones:
            route = self.optimize_route_by_zone(zone, bins_per_route)
            if route['bins']:
                daily_routes.append(route)
        
        return daily_routes


# =============================================
# TESTING FUNCTION
# =============================================

def test_route_optimizer():
    """Test the route optimizer"""
    print("=" * 70)
    print("AI Route Optimizer - Test Results")
    print("=" * 70)
    
    optimizer = RouteOptimizer()
    
    # Test 1: Optimize specific bins
    print("\n[Test 1] Optimizing route for bins needing collection...")
    bin_ids = [1, 3, 6, 7, 10]  # Example bin IDs
    
    route = optimizer.optimize_route(bin_ids)
    
    print(f"\nOptimized Route:")
    print(f"Total Bins: {route['total_bins']}")
    print(f"Total Distance: {route['total_distance']} km")
    print(f"Average Waste Level: {route['average_waste_level']}%")
    print(f"Method: {route['optimization_method']}")
    
    print("\nRoute Sequence:")
    print("-" * 70)
    for bin_stop in route['bins']:
        print(f"{bin_stop['sequence']}. {bin_stop['bin_code']} - {bin_stop['location']}")
        print(f"   Waste Level: {bin_stop['waste_level']}% | Distance: {bin_stop['distance_from_previous']} km")
    
    # Test 2: Create routes for all zones
    print("\n" + "=" * 70)
    print("[Test 2] Creating daily routes for all zones...")
    print("=" * 70)
    
    daily_routes = optimizer.create_daily_routes(bins_per_route=6)
    
    for idx, route in enumerate(daily_routes, 1):
        print(f"\nRoute {idx} - {route['zone']}")
        print(f"  Bins: {route['total_bins']}")
        print(f"  Distance: {route['total_distance']} km")
        print(f"  Stops: ", end="")
        print(", ".join([b['bin_code'] for b in route['bins']]))
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    test_route_optimizer()
