"""
Citizen feedback analytics service for waste management system.
Tracks citizen engagement, feedback sentiment, complaints, and satisfaction metrics.
"""
from database import Database
from datetime import datetime, timedelta


class CitizenFeedbackService:
    """Provides citizen feedback analytics and insights."""
    
    def __init__(self):
        self.db = Database()
    
    def get_feedback_overview(self, days=30):
        """Get overall citizen feedback overview."""    
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                COUNT(*) as total_feedback,
                SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as positive_feedback,
                SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) as neutral_feedback,
                SUM(CASE WHEN rating < 3 THEN 1 ELSE 0 END) as negative_feedback,
                AVG(rating) as avg_rating
            FROM citizen_feedback
            WHERE created_at >= %s
            """
            
            self.db.cursor.execute(query, (start_date,))
            row = self.db.cursor.fetchone()
            
            total = row[0] or 1
            positive = row[1] or 0
            neutral = row[2] or 0
            negative = row[3] or 0
            avg_rating = row[4] or 0
            
            # Calculate sentiment score (0-100)
            sentiment_score = ((positive - negative) / total * 100) + 50 if total > 0 else 50
            sentiment_score = max(0, min(100, sentiment_score))
            
            return {
                'success': True,
                'total_feedback_received': total,
                'positive_feedback': positive,
                'neutral_feedback': neutral,
                'negative_feedback': negative,
                'positive_percent': round((positive / total * 100), 1) if total > 0 else 0,
                'avg_rating': round(avg_rating, 2),
                'sentiment_score': round(sentiment_score, 1),
                'sentiment_status': 'Excellent' if sentiment_score >= 80 else 'Good' if sentiment_score >= 60 else 'Fair' if sentiment_score >= 40 else 'Poor'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_complaint_summary(self, days=30):
        """Get complaint categories and resolution status."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                category,
                COUNT(*) as complaint_count,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_count,
                AVG(DATEDIFF(resolved_date, created_at)) as avg_resolution_days
            FROM citizen_complaints
            WHERE created_at >= %s
            GROUP BY category
            ORDER BY complaint_count DESC
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            complaints = []
            for row in rows:
                total = row[1] or 1
                resolved = row[2] or 0
                resolution_rate = (resolved / total * 100)
                
                complaints.append({
                    'category': row[0],
                    'total_complaints': total,
                    'resolved': resolved,
                    'pending': row[3] or 0,
                    'in_progress': row[4] or 0,
                    'resolution_rate_percent': round(resolution_rate, 1),
                    'avg_resolution_days': round(row[5] or 0, 1)
                })
            
            return {
                'success': True,
                'complaints_by_category': complaints,
                'total_complaints': sum(c['total_complaints'] for c in complaints)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_satisfaction_trends(self, days=30):
        """Get satisfaction rating trends over time."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                DATE(created_at) as feedback_date,
                COUNT(*) as feedback_count,
                AVG(rating) as avg_rating,
                SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN rating < 3 THEN 1 ELSE 0 END) as negative_count
            FROM citizen_feedback
            WHERE created_at >= %s
            GROUP BY DATE(created_at)
            ORDER BY feedback_date DESC
            LIMIT 14
            """
            
            self.db.cursor.execute(query, (start_date,))
            rows = self.db.cursor.fetchall()
            
            trends = []
            for row in rows:
                feedback_count = row[1] or 1
                positive_pct = (row[3] / feedback_count * 100) if feedback_count > 0 else 0
                
                trends.append({
                    'date': str(row[0]),
                    'feedback_count': feedback_count,
                    'avg_rating': round(row[2] or 0, 2),
                    'positive_percent': round(positive_pct, 1),
                    'negative_count': row[4] or 0
                })
            
            return {
                'success': True,
                'trends': trends
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_feedback_topics(self, days=30, limit=10):
        """Get most mentioned feedback topics."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                topic,
                COUNT(*) as mention_count,
                AVG(rating) as avg_rating,
                SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as positive_mentions
            FROM citizen_feedback
            WHERE created_at >= %s AND topic IS NOT NULL
            GROUP BY topic
            ORDER BY mention_count DESC
            LIMIT %s
            """
            
            self.db.cursor.execute(query, (start_date, limit))
            rows = self.db.cursor.fetchall()
            
            topics = []
            for row in rows:
                mention_count = row[1] or 1
                positive = row[3] or 0
                positive_pct = (positive / mention_count * 100)
                
                topics.append({
                    'topic': row[0],
                    'mention_count': mention_count,
                    'avg_rating': round(row[2] or 0, 2),
                    'positive_sentiment_percent': round(positive_pct, 1)
                })
            
            return {
                'success': True,
                'topics': topics
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_citizen_engagement(self, days=30):
        """Get citizen engagement metrics."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                COUNT(DISTINCT user_id) as active_citizens,
                COUNT(*) as total_interactions,
                SUM(CASE WHEN action_type = 'report_waste' THEN 1 ELSE 0 END) as waste_reports,
                SUM(CASE WHEN action_type = 'provide_feedback' THEN 1 ELSE 0 END) as feedback_submissions,
                SUM(CASE WHEN action_type = 'submit_complaint' THEN 1 ELSE 0 END) as complaints_filed,
                AVG(engagement_score) as avg_engagement_score
            FROM citizen_engagement_log
            WHERE created_at >= %s
            """
            
            self.db.cursor.execute(query, (start_date,))
            row = self.db.cursor.fetchone()
            
            return {
                'success': True,
                'active_citizens': row[0] or 0,
                'total_interactions': row[1] or 0,
                'waste_reports_filed': row[2] or 0,
                'feedback_submissions': row[3] or 0,
                'complaints_filed': row[4] or 0,
                'avg_engagement_score': round(row[5] or 0, 1)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_feedback_recommendations(self, days=30):
        """Get recommendations based on citizen feedback."""
        try:
            overview = self.get_feedback_overview(days)
            if not overview.get('success'):
                return overview
            
            complaints = self.get_complaint_summary(days)
            topics = self.get_feedback_topics(days)
            
            recommendations = []
            
            # Check sentiment
            if overview.get('sentiment_score', 0) < 50:
                recommendations.append({
                    'priority': 'CRITICAL',
                    'category': 'Service Quality',
                    'recommendation': f'Sentiment score is low ({overview.get("sentiment_score")}). Review complaints and address root causes.',
                    'action': 'Investigate top complaints and improve processes'
                })
            
            # Check complaint resolution rate
            if complaints.get('success'):
                for complaint in complaints.get('complaints_by_category', [])[:3]:
                    resolution_rate = complaint.get('resolution_rate_percent', 0)
                    if resolution_rate < 70:
                        recommendations.append({
                            'priority': 'HIGH',
                            'category': f'Complaint Resolution - {complaint.get("category")}',
                            'recommendation': f'Resolution rate is {resolution_rate}%. Accelerate resolution process.',
                            'action': 'Allocate more resources to complaint resolution'
                        })
            
            # Check negative feedback percentage
            negative_pct = (overview.get('negative_feedback', 0) / max(overview.get('total_feedback_received', 1), 1)) * 100
            if negative_pct > 20:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Feedback Management',
                    'recommendation': f'Negative feedback is {negative_pct:.1f}%. Prioritize improvement areas.',
                    'action': 'Analyze negative feedback for patterns and improvements'
                })
            
            return {
                'success': True,
                'recommendations': recommendations,
                'recommendation_count': len(recommendations)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
