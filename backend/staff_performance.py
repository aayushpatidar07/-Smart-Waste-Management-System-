"""
Staff performance analytics and insights service.
Tracks staff efficiency, collection performance, and performance metrics.
"""
from database import Database
from datetime import datetime, timedelta


class StaffPerformanceService:
    """Provides staff performance analytics and insights."""
    
    def __init__(self):
        self.db = Database()
    
    def get_staff_overview(self, days=30):
        """Get overall staff performance overview."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                COUNT(DISTINCT user_id) as total_staff,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_staff,
                SUM(CASE WHEN role = 'STAFF' THEN 1 ELSE 0 END) as collection_staff,
                SUM(CASE WHEN role = 'DRIVER' THEN 1 ELSE 0 END) as drivers
            FROM users
            WHERE role IN ('STAFF', 'DRIVER')
            """
            
            self.db.cursor.execute(query)
            row = self.db.cursor.fetchone()
            
            # Get performance stats for period
            perf_query = """
            SELECT 
                COUNT(*) as total_collections,
                AVG(CASE WHEN weight_kg > 0 THEN weight_kg ELSE NULL END) as avg_weight,
                SUM(weight_kg) as total_weight,
                COUNT(DISTINCT staff_id) as staff_assigned
            FROM collection_logs
            WHERE collection_date >= %s AND status = 'completed'
            """
            
            self.db.cursor.execute(perf_query, (start_date,))
            perf = self.db.cursor.fetchone()
            
            collections = perf[0] or 1
            avg_weight = perf[1] or 0
            total_weight = perf[2] or 0
            
            return {
                'success': True,
                'total_staff': row[0],
                'active_staff': row[1] or 0,
                'collection_staff': row[2] or 0,
                'drivers': row[3] or 0,
                'total_collections': collections,
                'avg_weight_per_collection': round(avg_weight, 2),
                'total_weight_handled': round(total_weight, 2),
                'staff_assigned_to_collections': perf[3] or 0
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_top_performers(self, days=30, limit=10):
        """Get top performing staff members."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                u.id,
                u.name,
                u.role,
                COUNT(cl.id) as collections,
                SUM(cl.weight_kg) as total_weight,
                COUNT(DISTINCT cl.collection_date) as days_worked,
                AVG(cl.weight_kg) as avg_per_collection
            FROM collection_logs cl
            JOIN users u ON cl.staff_id = u.id
            WHERE cl.collection_date >= %s AND cl.status = 'completed'
            GROUP BY u.id, u.name, u.role
            ORDER BY collections DESC
            LIMIT %s
            """
            
            self.db.cursor.execute(query, (start_date, limit))
            rows = self.db.cursor.fetchall()
            
            performers = []
            for row in rows:
                performers.append({
                    'staff_id': row[0],
                    'staff_name': row[1],
                    'role': row[2],
                    'total_collections': row[3],
                    'total_weight_kg': round(row[4] or 0, 2),
                    'days_worked': row[5],
                    'avg_per_collection_kg': round(row[6] or 0, 2),
                    'efficiency_score': round((row[3] / max(row[5], 1)) * 10, 1)
                })
            
            return {
                'success': True,
                'top_performers': performers
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_staff_efficiency_metrics(self, days=30):
        """Get efficiency metrics by staff member."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                u.id,
                u.name,
                COUNT(cl.id) as collections,
                AVG(cl.vehicle_distance_km) as avg_route_distance,
                AVG(cl.weight_kg) as avg_weight,
                COUNT(DISTINCT cl.collection_date) as days_active,
                SUM(CASE WHEN cl.status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN cl.status != 'completed' THEN 1 ELSE 0 END) as issues
            FROM collection_logs cl
            JOIN users u ON cl.staff_id = u.id
            WHERE cl.collection_date >= %s AND u.role IN ('STAFF', 'DRIVER')
            GROUP BY u.id, u.name
            ORDER BY completed DESC
            LIMIT 20
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            metrics = []
            for row in rows:
                collections = row[2] or 0
                completed = row[6] or 0
                success_rate = (completed / max(collections, 1)) * 100
                
                metrics.append({
                    'staff_id': row[0],
                    'staff_name': row[1],
                    'total_collections': collections,
                    'avg_route_distance_km': round(row[3] or 0, 2),
                    'avg_weight_per_collection_kg': round(row[4] or 0, 2),
                    'days_active': row[5],
                    'completed_collections': completed,
                    'collections_with_issues': row[7],
                    'success_rate_percent': round(success_rate, 1)
                })
            
            return {
                'success': True,
                'metrics': metrics
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_performance_trends(self, days=30):
        """Get daily performance trends."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                DATE(collection_date) as date,
                COUNT(*) as collections,
                COUNT(DISTINCT staff_id) as staff_deployed,
                AVG(weight_kg) as avg_weight,
                COUNT(DISTINCT collection_date) as unique_dates,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status != 'completed' THEN 1 ELSE 0 END) as with_issues
            FROM collection_logs
            WHERE collection_date >= %s
            GROUP BY DATE(collection_date)
            ORDER BY date DESC
            LIMIT 14
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            trends = []
            for row in rows:
                collections = row[1] or 1
                completed = row[5] or 0
                success_rate = (completed / collections) * 100
                
                trends.append({
                    'date': str(row[0]),
                    'collections': collections,
                    'staff_deployed': row[2],
                    'avg_weight_per_collection_kg': round(row[3] or 0, 2),
                    'completed_collections': completed,
                    'with_issues': row[6],
                    'success_rate_percent': round(success_rate, 1)
                })
            
            return {
                'success': True,
                'trends': trends
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_staff_ratings(self, days=30):
        """Get staff member ratings and leaderboard."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                u.id,
                u.name,
                COUNT(cl.id) as assignments,
                AVG(cl.weight_kg) as avg_weight,
                COUNT(DISTINCT cl.collection_date) as days_worked,
                COUNT(DISTINCT DATE(cl.collection_date)) as unique_days,
                SUM(CASE WHEN cl.status = 'completed' THEN 1 ELSE 0 END) as successful
            FROM collection_logs cl
            JOIN users u ON cl.staff_id = u.id
            WHERE cl.collection_date >= %s AND u.role IN ('STAFF', 'DRIVER')
            GROUP BY u.id, u.name
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            ratings = []
            for row in rows:
                assignments = row[2] or 1
                successful = row[6] or 0
                avg_weight = row[3] or 0
                
                # Rating: 0-100 based on completion rate and assignments
                completion_rate = (successful / assignments) * 100
                volume_score = min((assignments / 20) * 50, 50)  # Cap at 50 for 20+ assignments
                efficiency_score = min((avg_weight / 1000) * 50, 50)  # Cap at 50 for 1000kg avg
                
                overall_rating = round((completion_rate * 0.5) + (volume_score * 0.3) + (efficiency_score * 0.2), 1)
                
                ratings.append({
                    'staff_id': row[0],
                    'staff_name': row[1],
                    'assignments': assignments,
                    'successful_assignments': successful,
                    'completion_rate': round(completion_rate, 1),
                    'avg_weight_kg': round(avg_weight, 2),
                    'days_active': row[5],
                    'rating': overall_rating,
                    'rank': ''  # Will be filled after sorting
                })
            
            # Sort by rating and assign ranks
            ratings.sort(key=lambda x: x['rating'], reverse=True)
            for idx, rating in enumerate(ratings):
                if idx < len(ratings) // 3:
                    rating['rank'] = 'Gold'
                elif idx < 2 * len(ratings) // 3:
                    rating['rank'] = 'Silver'
                else:
                    rating['rank'] = 'Bronze'
            
            return {
                'success': True,
                'ratings': ratings
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_performance_recommendations(self, days=30):
        """Get performance improvement recommendations."""
        try:
            overview = self.get_staff_overview(days)
            if not overview.get('success'):
                return overview
            
            metrics = self.get_staff_efficiency_metrics(days)
            trends = self.get_performance_trends(days)
            
            recommendations = []
            
            # Check for low success rates
            for metric in metrics.get('metrics', [])[:5]:
                if metric.get('success_rate_percent', 0) < 85:
                    recommendations.append({
                        'priority': 'HIGH',
                        'category': 'Staff Support',
                        'staff_name': metric.get('staff_name'),
                        'recommendation': f'Success rate is {metric.get("success_rate_percent")}%. Provide additional training or support.',
                        'action': 'Schedule performance review and training'
                    })
            
            # Check for workload imbalance
            performers = self.get_top_performers(days, limit=2)
            if performers.get('top_performers'):
                top_collections = performers['top_performers'][0].get('total_collections', 0)
                overview_assignments = overview.get('total_collections', 1)
                avg_per_staff = overview_assignments / max(overview.get('staff_assigned_to_collections', 1), 1)
                
                if top_collections > avg_per_staff * 1.5:
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'category': 'Workload Balance',
                        'recommendation': 'Workload is unevenly distributed. Consider balancing assignments.',
                        'action': 'Review scheduling and workload distribution'
                    })
            
            # Check for team utilization
            if overview.get('staff_assigned_to_collections', 0) < overview.get('total_staff', 1) * 0.7:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Staff Utilization',
                    'recommendation': f'Only {(overview.get("staff_assigned_to_collections", 0) / max(overview.get("total_staff", 1), 1) * 100):.0f}% of staff assigned. Increase engagement.',
                    'action': 'Review scheduling and assignments'
                })
            
            return {
                'success': True,
                'recommendations': recommendations,
                'recommendation_count': len(recommendations)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
