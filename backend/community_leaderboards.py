"""Community Engagement & Leaderboards Service
Tracks citizen participation, waste reporting contributions, and gamification
metrics to encourage community involvement in waste management.
"""

from datetime import datetime, timedelta
from models import Database

class CommunityLeaderboardsService:
    """Service for managing community engagement and leaderboards"""
    
    def __init__(self):
        self.db = Database()
    
    def get_citizen_leaderboard(self, days=30, limit=20):
        """
        Get top citizen contributors by number of reports
        
        Args:
            days: Time period for leaderboard
            limit: Number of top users to return
        
        Returns:
            Ranked list of citizen contributors
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get top reporters
            query = """
                SELECT 
                    u.id, u.name, u.email,
                    COUNT(wr.id) as reports_count,
                    SUM(wr.waste_quantity) as total_waste_kg,
                    COUNT(DISTINCT DATE(wr.created_at)) as active_days
                FROM users u
                LEFT JOIN waste_reports wr ON u.id = wr.reported_by AND wr.created_at >= %s
                WHERE u.role = 'citizen'
                GROUP BY u.id, u.name, u.email
                HAVING reports_count > 0
                ORDER BY reports_count DESC
                LIMIT %s
            """
            
            cursor.execute(query, (cutoff_date, limit))
            citizens = cursor.fetchall()
            
            # Add rankings
            leaderboard = []
            for idx, citizen in enumerate(citizens):
                leaderboard.append({
                    'rank': idx + 1,
                    'citizen_id': citizen['id'],
                    'name': citizen['name'],
                    'reports': citizen['reports_count'],
                    'total_waste_kg': round(citizen['total_waste_kg'] or 0, 2),
                    'active_days': citizen['active_days']
                })
            
            cursor.close()
            
            return {
                'success': True,
                'period_days': days,
                'total_participators': len(leaderboard),
                'leaderboard': leaderboard
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_zone_leaderboard(self, limit=15):
        """
        Get top performing zones by waste collection efficiency
        
        Args:
            limit: Number of zones to return
        
        Returns:
            Ranked zones with performance metrics
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Get zone performance
            query = """
                SELECT 
                    b.zone_id,
                    COUNT(DISTINCT b.id) as total_bins,
                    AVG(b.fill_level) as avg_fill,
                    SUM(wr.waste_quantity) as total_waste_collected,
                    COUNT(wr.id) as collections_30d
                FROM bins b
                LEFT JOIN waste_reports wr ON b.id = wr.bin_id 
                    AND wr.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                WHERE b.zone_id IS NOT NULL
                GROUP BY b.zone_id
                ORDER BY total_waste_collected DESC
                LIMIT %s
            """
            
            cursor.execute(query, (limit,))
            zones = cursor.fetchall()
            
            # Calculate performance scores
            leaderboard = []
            for idx, zone in enumerate(zones):
                # Score based on collection frequency and waste volume
                score = min(100, (zone['collections_30d'] / (zone['total_bins'] or 1)) * 10)
                
                leaderboard.append({
                    'rank': idx + 1,
                    'zone_id': zone['zone_id'],
                    'total_bins': zone['total_bins'],
                    'avg_fill_level': round(zone['avg_fill'], 1),
                    'total_waste_collected_kg': round(zone['total_waste_collected'] or 0, 2),
                    'collections_30d': zone['collections_30d'],
                    'performance_score': round(score, 1)
                })
            
            cursor.close()
            
            return {
                'success': True,
                'total_zones': len(leaderboard),
                'leaderboard': leaderboard
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_citizen_stats(self, citizen_id):
        """
        Get comprehensive statistics for a specific citizen
        
        Args:
            citizen_id: ID of the citizen
        
        Returns:
            Citizen engagement statistics and achievements
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Get citizen info
            user_query = "SELECT name, email FROM users WHERE id = %s AND role = 'citizen'"
            cursor.execute(user_query, (citizen_id,))
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                return {'success': False, 'message': 'Citizen not found'}
            
            # Get report stats
            stats_query = """
                SELECT 
                    COUNT(id) as total_reports,
                    SUM(waste_quantity) as total_waste,
                    AVG(waste_quantity) as avg_waste,
                    DATE(MAX(created_at)) as last_report_date,
                    COUNT(DISTINCT DATE(created_at)) as active_days,
                    COUNT(DISTINCT MONTH(created_at)) as active_months
                FROM waste_reports
                WHERE reported_by = %s
            """
            cursor.execute(stats_query, (citizen_id,))
            stats = cursor.fetchone()
            
            # Calculate contributing level
            total_reports = stats['total_reports'] or 0
            if total_reports >= 50:
                level = 'Platinum'
                badge = '⭐⭐⭐'
            elif total_reports >= 25:
                level = 'Gold'
                badge = '⭐⭐'
            elif total_reports >= 10:
                level = 'Silver'
                badge = '⭐'
            else:
                level = 'Bronze'
                badge = '•'
            
            cursor.close()
            
            return {
                'success': True,
                'citizen_id': citizen_id,
                'name': user['name'],
                'email': user['email'],
                'contributing_level': level,
                'badge': badge,
                'total_reports': total_reports,
                'total_waste_reported_kg': round(stats['total_waste'] or 0, 2),
                'average_waste_per_report_kg': round(stats['avg_waste'] or 0, 2),
                'active_days': stats['active_days'] or 0,
                'active_months': stats['active_months'] or 0,
                'last_report_date': stats['last_report_date'].isoformat() if stats['last_report_date'] else 'Never'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_contribution_timeline(self, citizen_id, days=60):
        """
        Get citizen contribution timeline showing reporting activity
        
        Args:
            citizen_id: ID of the citizen
            days: Number of days to analyze
        
        Returns:
            Daily contribution data for timeline visualization
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get daily contributions
            query = """
                SELECT 
                    DATE(created_at) as report_date,
                    COUNT(id) as reports_count,
                    SUM(waste_quantity) as daily_waste
                FROM waste_reports
                WHERE reported_by = %s AND created_at >= %s
                GROUP BY DATE(created_at)
                ORDER BY report_date DESC
                LIMIT %s
            """
            
            cursor.execute(query, (citizen_id, cutoff_date, days))
            timeline = cursor.fetchall()
            
            # Format timeline
            formatted_timeline = []
            for entry in timeline:
                formatted_timeline.append({
                    'date': entry['report_date'].isoformat(),
                    'reports': entry['reports_count'],
                    'waste_kg': round(entry['daily_waste'], 2)
                })
            
            cursor.close()
            
            return {
                'success': True,
                'citizen_id': citizen_id,
                'period_days': days,
                'total_entries': len(formatted_timeline),
                'timeline': formatted_timeline
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_community_achievements(self):
        """
        Get system-wide community achievements and milestones
        
        Returns:
            Community-wide statistics and milestone information
        """
        try:
            cursor = self.db.get_connection().cursor(dictionary=True)
            
            # Total citizens
            citizen_query = "SELECT COUNT(id) as total FROM users WHERE role = 'citizen'"
            cursor.execute(citizen_query)
            total_citizens = cursor.fetchone()['total']
            
            # Total reports
            report_query = "SELECT COUNT(id) as total, SUM(waste_quantity) as total_waste FROM waste_reports"
            cursor.execute(report_query)
            report_stats = cursor.fetchone()
            
            # Active citizens this month
            active_query = """
                SELECT COUNT(DISTINCT reported_by) as active_citizens
                FROM waste_reports
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """
            cursor.execute(active_query)
            active_citizens = cursor.fetchone()['active_citizens']
            
            cursor.close()
            
            # Calculate achievements
            achievements = []
            
            if total_citizens >= 100:
                achievements.append({'name': 'Community Milestone', 'desc': f'{total_citizens} Citizens Engaged', 'icon': '👥'})
            
            if report_stats['total'] >= 1000:
                achievements.append({'name': 'Volume Champion', 'desc': f'{round(report_stats["total_waste"] or 0, 0):.0f} kg Reported', 'icon': '🏆'})
            
            if active_citizens >= 30:
                achievements.append({'name': 'Active Community', 'desc': f'{active_citizens} Active Contributors', 'icon': '⚡'})
            
            return {
                'success': True,
                'total_community_members': total_citizens,
                'total_reports_submitted': report_stats['total'],
                'total_waste_reported_kg': round(report_stats['total_waste'] or 0, 2),
                'active_contributors_month': active_citizens,
                'achievements': achievements,
                'engagement_rate': round((active_citizens / total_citizens * 100) if total_citizens > 0 else 0, 1)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Initialize service
community_leaderboards_service = CommunityLeaderboardsService()
