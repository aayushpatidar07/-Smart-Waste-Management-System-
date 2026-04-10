"""Schedule Optimization Service
Analyzes waste collection patterns and provides intelligent scheduling recommendations
to optimize efficiency, reduce costs, and improve service delivery.
"""

from datetime import datetime, timedelta
import json
from models import Database
from statistics import mean, stdev

class ScheduleOptimizationService:
    """Service for optimizing collection schedules and route planning"""
    
    def __init__(self):
        self.db = Database()
    
    def analyze_collection_patterns(self, days=30):
        """
        Analyze historical collection patterns to identify trends
        
        Args:
            days: Number of days of historical data to analyze
        
        Returns:
            Collection pattern analysis with frequency and timing insights
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get collection history
            query = """
                SELECT 
                    DATE(created_at) as collection_date,
                    HOUR(created_at) as hour,
                    COUNT(*) as collection_count,
                    AVG(waste_quantity) as avg_waste,
                    SUM(waste_quantity) as total_waste
                FROM waste_reports
                WHERE created_at >= %s
                GROUP BY DATE(created_at), HOUR(created_at)
                ORDER BY collection_date, hour
            """
            
            cursor.execute(query, (cutoff_date,))
            collections = cursor.fetchall()
            
            if not collections:
                cursor.close()
                return {
                    'success': False,
                    'message': 'Insufficient historical data for analysis'
                }
            
            # Calculate statistics by hour
            hourly_stats = {}
            for collection in collections:
                hour = collection['hour']
                if hour not in hourly_stats:
                    hourly_stats[hour] = []
                hourly_stats[hour].append(collection['collection_count'])
            
            # Identify peak and low hours
            peak_hours = []
            low_hours = []
            for hour, counts in hourly_stats.items():
                avg_count = mean(counts)
                if avg_count > 5:  # Peak threshold
                    peak_hours.append({'hour': hour, 'avg_count': round(avg_count, 2)})
                elif avg_count < 2:  # Low threshold
                    low_hours.append({'hour': hour, 'avg_count': round(avg_count, 2)})
            
            peak_hours.sort(key=lambda x: x['avg_count'], reverse=True)
            low_hours.sort(key=lambda x: x['avg_count'])
            
            cursor.close()
            
            return {
                'success': True,
                'analysis_period_days': days,
                'total_collections': len(collections),
                'peak_hours': peak_hours[:5],
                'low_activity_hours': low_hours[:5],
                'recommendation': 'Schedule collections during peak hours to maximize efficiency or consolidate routes during low hours'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_optimal_collection_windows(self, zone_id=None):
        """
        Determine optimal time windows for collection based on historical fill rates
        
        Args:
            zone_id: Optional zone ID to narrow optimization
        
        Returns:
            Recommended collection windows with efficiency scores
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Analyze bin fill rates
            if zone_id:
                query = """
                    SELECT 
                        id,
                        HOUR(created_at) as hour,
                        AVG(fill_level) as avg_fill,
                        MAX(fill_level) as max_fill,
                        COUNT(*) as readings
                    FROM bins
                    WHERE zone_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                    GROUP BY id, HOUR(created_at)
                    ORDER BY hour
                """
                cursor.execute(query, (zone_id,))
            else:
                query = """
                    SELECT 
                        id,
                        HOUR(created_at) as hour,
                        AVG(fill_level) as avg_fill,
                        MAX(fill_level) as max_fill,
                        COUNT(*) as readings
                    FROM bins
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                    GROUP BY id, HOUR(created_at)
                    ORDER BY hour
                """
                cursor.execute(query)
            
            results = cursor.fetchall()
            
            if not results:
                cursor.close()
                return {
                    'success': False,
                    'message': 'Insufficient bin data for optimization'
                }
            
            # Calculate window scores
            windows = {}
            optimal_window = None
            best_score = 0
            
            for result in results:
                hour = result['hour']
                if hour not in windows:
                    windows[hour] = {
                        'hour': hour,
                        'avg_fill': 0,
                        'count': 0
                    }
                windows[hour]['avg_fill'] += result['avg_fill']
                windows[hour]['count'] += 1
            
            # Calculate efficiency scores
            for hour, data in windows.items():
                avg_fill = data['avg_fill'] / data['count']
                # Score based on fill level around 70-80% for optimal pickup
                score = 100 - abs(75 - avg_fill)
                windows[hour]['efficiency_score'] = round(score, 1)
                
                if score > best_score and avg_fill > 50:
                    best_score = score
                    optimal_window = hour
            
            # Sort by efficiency
            sorted_windows = sorted(windows.items(), key=lambda x: x[1]['efficiency_score'], reverse=True)
            
            cursor.close()
            
            return {
                'success': True,
                'optimal_window_hour': optimal_window,
                'recommended_windows': [
                    {
                        'hour': h,
                        'efficiency_score': w['efficiency_score'],
                        'avg_fill_level': round(w['avg_fill'] / w['count'], 1)
                    }
                    for h, w in sorted_windows[:5]
                ],
                'recommendation': f'Primary collection window: {optimal_window}:00 (highest efficiency). Secondary options available.'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def calculate_route_efficiency(self, route_id):
        """
        Calculate efficiency metrics for a specific route
        
        Args:
            route_id: ID of the route to analyze
        
        Returns:
            Route efficiency with recommendations for improvement
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Get route details
            route_query = """
                SELECT 
                    id, name, distance, duration,
                    bins_allocated, status, created_at
                FROM routes
                WHERE id = %s
            """
            cursor.execute(route_query, (route_id,))
            route = cursor.fetchone()
            
            if not route:
                cursor.close()
                return {'success': False, 'message': 'Route not found'}
            
            # Get collection history for this route
            history_query = """
                SELECT 
                    COUNT(*) as total_collections,
                    AVG(bins_serviced) as avg_bins_serviced,
                    AVG(collection_time) as avg_collection_time,
                    SUM(waste_collected) as total_waste
                FROM waste_reports
                WHERE route_id = %s
                AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            cursor.execute(history_query, (route_id,))
            history = cursor.fetchone()
            
            # Calculate efficiency metrics
            efficiency_score = 100
            recommendations = []
            
            if history and history['total_collections'] > 0:
                utilization = (history['avg_bins_serviced'] / route['bins_allocated'] * 100) if route['bins_allocated'] > 0 else 0
                
                if utilization < 70:
                    efficiency_score -= 20
                    recommendations.append('Route is underutilized. Consider consolidating with adjacent routes.')
                elif utilization > 95:
                    efficiency_score -= 15
                    recommendations.append('Route is over-capacity. Consider splitting into multiple routes.')
                
                time_per_bin = history['avg_collection_time'] / history['avg_bins_serviced'] if history['avg_bins_serviced'] > 0 else 0
                if time_per_bin > 10:  # 10 minutes threshold
                    efficiency_score -= 10
                    recommendations.append('Collection time per bin is high. Verify route sequence optimization.')
                
            if not recommendations:
                recommendations = ['Route is operating efficiently. Maintain current schedule.']
            
            cursor.close()
            
            return {
                'success': True,
                'route_id': route_id,
                'route_name': route['name'],
                'efficiency_score': round(max(0, efficiency_score), 1),
                'utilization_percent': round(utilization if history else 0, 1),
                'total_collections_30d': history['total_collections'] if history else 0,
                'total_waste_collected_kg': round(history['total_waste'] if history else 0, 2),
                'recommendations': recommendations
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def optimize_route_sequence(self, route_id):
        """
        Analyze route sequence and suggest optimization
        
        Args:
            route_id: ID of route to optimize
        
        Returns:
            Optimized sequence suggestions with efficiency gains
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Get bins on this route
            bins_query = """
                SELECT 
                    id, zone_id, latitude, longitude, 
                    fill_level, location_name
                FROM bins
                WHERE route_id = %s
                ORDER BY zone_id, id
            """
            cursor.execute(bins_query, (route_id,))
            bins = cursor.fetchall()
            
            if not bins:
                cursor.close()
                return {'success': False, 'message': 'No bins assigned to this route'}
            
            # Group by zone for optimization
            zones = {}
            for bin_data in bins:
                zone_id = bin_data['zone_id']
                if zone_id not in zones:
                    zones[zone_id] = []
                zones[zone_id].append(bin_data)
            
            # Sort by fill level within each zone (highest first)
            optimization = []
            total_bins = 0
            for zone_id, zone_bins in sorted(zones.items()):
                sorted_bins = sorted(zone_bins, key=lambda x: x['fill_level'], reverse=True)
                for bin_item in sorted_bins:
                    optimization.append({
                        'bin_id': bin_item['id'],
                        'zone_id': bin_item['zone_id'],
                        'fill_level': bin_item['fill_level'],
                        'location': bin_item['location_name']
                    })
                    total_bins += 1
            
            cursor.close()
            
            return {
                'success': True,
                'route_id': route_id,
                'total_bins': total_bins,
                'total_zones': len(zones),
                'optimized_sequence': optimization[:20],  # Return first 20 for preview
                'efficiency_gain_percent': round((len(zones) / total_bins) * 100, 1) if total_bins > 0 else 0,
                'recommendation': f'Proposed sequence prioritizes high-fill bins within {len(zones)} zones for faster processing.'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_scheduling_recommendations(self):
        """
        Generate comprehensive scheduling recommendations for the entire system
        
        Returns:
            System-wide scheduling optimization recommendations
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            recommendations = []
            
            # Analyze vehicle utilization
            vehicle_query = """
                SELECT 
                    COUNT(*) as total_vehicles,
                    AVG(current_trips) as avg_trips,
                    AVG(fuel_consumption) as avg_fuel
                FROM vehicles
            """
            cursor.execute(vehicle_query)
            vehicles = cursor.fetchone()
            
            if vehicles['avg_trips'] < 3:
                recommendations.append({
                    'priority': 'High',
                    'category': 'Vehicle Utilization',
                    'recommendation': f'Average trips per vehicle is {vehicles["avg_trips"]}. Consolidate routes to increase utilization.'
                })
            
            # Analyze bin fullness patterns
            bin_query = """
                SELECT 
                    AVG(fill_level) as avg_fill,
                    MAX(fill_level) as max_fill,
                    COUNT(*) as total_bins
                FROM bins
            """
            cursor.execute(bin_query)
            bins = cursor.fetchone()
            
            if bins['avg_fill'] > 85:
                recommendations.append({
                    'priority': 'Critical',
                    'category': 'Overflow Risk',
                    'recommendation': f'System average fill level is {bins["avg_fill"]}%. Increase collection frequency to prevent overflow.'
                })
            elif bins['avg_fill'] < 40:
                recommendations.append({
                    'priority': 'Medium',
                    'category': 'Under-collection',
                    'recommendation': f'System average fill level is {bins["avg_fill"]}%. Reduce collection frequency to save costs.'
                })
            
            # Analyze collection distribution
            hour_query = """
                SELECT 
                    HOUR(created_at) as hour,
                    COUNT(*) as collection_count
                FROM waste_reports
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY HOUR(created_at)
            """
            cursor.execute(hour_query)
            hours = cursor.fetchall()
            
            if len(hours) > 0:
                avg_hourly = sum(h['collection_count'] for h in hours) / len(hours)
                max_hour = max(hours, key=lambda x: x['collection_count'])
                
                if max_hour['collection_count'] > avg_hourly * 2:
                    recommendations.append({
                        'priority': 'Medium',
                        'category': 'Collection Distribution',
                        'recommendation': f'Peak hour ({max_hour["hour"]}:00) has {max_hour["collection_count"]} collections. Spread collections across more hours.'
                    })
            
            cursor.close()
            
            # Add general recommendations
            recommendations.append({
                'priority': 'Low',
                'category': 'Best Practice',
                'recommendation': 'Review and update all route schedules on a weekly basis for continuous optimization.'
            })
            
            return {
                'success': True,
                'total_recommendations': len(recommendations),
                'recommendations': recommendations,
                'next_review_date': (datetime.now() + timedelta(days=7)).isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_vehicle_schedule(self, vehicle_id, days=7):
        """
        Get optimized vehicle schedule for specified period
        
        Args:
            vehicle_id: ID of vehicle
            days: Number of days to plan schedule
        
        Returns:
            Optimized vehicle schedule with assigned collections
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Get vehicle info
            vehicle_query = """
                SELECT 
                    id, name, vehicle_type, capacity,
                    current_trips, fuel_consumption
                FROM vehicles
                WHERE id = %s
            """
            cursor.execute(vehicle_query, (vehicle_id,))
            vehicle = cursor.fetchone()
            
            if not vehicle:
                cursor.close()
                return {'success': False, 'message': 'Vehicle not found'}
            
            # Get route assignments
            route_query = """
                SELECT 
                    id, name, distance, duration,
                    bins_allocated, status
                FROM routes
                WHERE vehicle_id = %s
                LIMIT 10
            """
            cursor.execute(route_query, (vehicle_id,))
            routes = cursor.fetchall()
            
            schedule = []
            for day in range(days):
                date = (datetime.now() + timedelta(days=day)).date()
                for idx, route in enumerate(routes):
                    schedule.append({
                        'date': date.isoformat(),
                        'shift': f'Shift {idx + 1}',
                        'route_id': route['id'],
                        'route_name': route['name'],
                        'distance_km': route['distance'],
                        'duration_hours': route['duration'],
                        'bins_to_service': route['bins_allocated']
                    })
            
            cursor.close()
            
            return {
                'success': True,
                'vehicle_id': vehicle_id,
                'vehicle_name': vehicle['name'],
                'schedule_period_days': days,
                'total_scheduled_collections': len(schedule),
                'schedule': schedule[:21],  # 3 weeks max
                'capacity_utilization': round(vehicle['capacity'], 0),
                'recommendation': 'Review and adjust schedule to match seasonal demand patterns.'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Initialize service
schedule_optimization_service = ScheduleOptimizationService()
