"""Report Quality Insights Service
Analyzes waste report completeness, resolution quality, and zone-level reporting patterns.
"""

from datetime import datetime, timedelta
from models import Database


class ReportQualityInsightsService:
    """Service class for report quality analytics."""

    def __init__(self):
        self.db = Database()

    def _connection(self):
        conn = self.db.connect()
        if not conn:
            raise Exception('Unable to connect to database')
        return conn

    def get_quality_overview(self, days=30):
        """Get high-level report quality metrics."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_reports,
                    SUM(CASE WHEN description IS NOT NULL AND TRIM(description) <> '' THEN 1 ELSE 0 END) AS reports_with_description,
                    SUM(CASE WHEN image_path IS NOT NULL AND TRIM(image_path) <> '' THEN 1 ELSE 0 END) AS reports_with_image,
                    SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) AS reports_with_location,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_reports,
                    SUM(CASE WHEN status IN ('pending', 'acknowledged') THEN 1 ELSE 0 END) AS open_reports,
                    SUM(CASE WHEN priority IN ('high', 'critical') THEN 1 ELSE 0 END) AS urgent_reports,
                    AVG(CASE WHEN resolved_at IS NOT NULL THEN TIMESTAMPDIFF(HOUR, reported_at, resolved_at) END) AS avg_resolution_hours
                FROM waste_reports
                WHERE reported_at >= %s
                """,
                (start_date,)
            )
            row = cursor.fetchone() or {}

            total = row.get('total_reports', 0) or 0
            desc_rate = round(((row.get('reports_with_description', 0) or 0) / total) * 100, 1) if total else 0
            image_rate = round(((row.get('reports_with_image', 0) or 0) / total) * 100, 1) if total else 0
            location_rate = round(((row.get('reports_with_location', 0) or 0) / total) * 100, 1) if total else 0
            resolution_rate = round(((row.get('resolved_reports', 0) or 0) / total) * 100, 1) if total else 0

            quality_score = min(100, round(desc_rate * 0.3 + image_rate * 0.2 + location_rate * 0.2 + resolution_rate * 0.3, 1))
            quality_status = 'Strong' if quality_score >= 75 else 'Watch' if quality_score >= 50 else 'Poor'

            return {
                'success': True,
                'period_days': days,
                'quality_score': quality_score,
                'quality_status': quality_status,
                'total_reports': total,
                'open_reports': row.get('open_reports', 0) or 0,
                'urgent_reports': row.get('urgent_reports', 0) or 0,
                'description_coverage': desc_rate,
                'image_coverage': image_rate,
                'location_coverage': location_rate,
                'resolution_rate': resolution_rate,
                'avg_resolution_hours': round(row.get('avg_resolution_hours', 0) or 0, 1)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_report_type_quality(self, days=30):
        """Get report quality metrics by report type."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    report_type,
                    COUNT(*) AS total_reports,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved_reports,
                    SUM(CASE WHEN description IS NOT NULL AND TRIM(description) <> '' THEN 1 ELSE 0 END) AS with_description,
                    SUM(CASE WHEN image_path IS NOT NULL AND TRIM(image_path) <> '' THEN 1 ELSE 0 END) AS with_image,
                    SUM(CASE WHEN priority IN ('high', 'critical') THEN 1 ELSE 0 END) AS urgent_reports
                FROM waste_reports
                WHERE reported_at >= %s
                GROUP BY report_type
                ORDER BY total_reports DESC
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            report_types = []
            for row in rows:
                total = row.get('total_reports', 0) or 0
                report_types.append({
                    'report_type': row.get('report_type'),
                    'total_reports': total,
                    'resolved_reports': row.get('resolved_reports', 0) or 0,
                    'resolution_rate': round(((row.get('resolved_reports', 0) or 0) / total) * 100, 1) if total else 0,
                    'description_coverage': round(((row.get('with_description', 0) or 0) / total) * 100, 1) if total else 0,
                    'image_coverage': round(((row.get('with_image', 0) or 0) / total) * 100, 1) if total else 0,
                    'urgent_reports': row.get('urgent_reports', 0) or 0
                })

            return {'success': True, 'period_days': days, 'types': report_types}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_zone_quality(self, days=30):
        """Get report quality profile by zone."""
        conn = None
        cursor = None
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            conn = self._connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    b.zone,
                    COUNT(wr.report_id) AS total_reports,
                    SUM(CASE WHEN wr.status = 'resolved' THEN 1 ELSE 0 END) AS resolved_reports,
                    SUM(CASE WHEN wr.status IN ('pending', 'acknowledged') THEN 1 ELSE 0 END) AS open_reports,
                    SUM(CASE WHEN wr.priority IN ('high', 'critical') THEN 1 ELSE 0 END) AS urgent_reports,
                    SUM(CASE WHEN wr.description IS NOT NULL AND TRIM(wr.description) <> '' THEN 1 ELSE 0 END) AS with_description,
                    SUM(CASE WHEN wr.image_path IS NOT NULL AND TRIM(wr.image_path) <> '' THEN 1 ELSE 0 END) AS with_image
                FROM waste_reports wr
                LEFT JOIN bins b ON b.bin_id = wr.bin_id
                WHERE wr.reported_at >= %s
                  AND b.zone IS NOT NULL
                  AND b.zone <> ''
                GROUP BY b.zone
                ORDER BY total_reports DESC
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            zones = []
            for row in rows:
                total = row.get('total_reports', 0) or 0
                zones.append({
                    'zone': row.get('zone'),
                    'total_reports': total,
                    'open_reports': row.get('open_reports', 0) or 0,
                    'urgent_reports': row.get('urgent_reports', 0) or 0,
                    'resolution_rate': round(((row.get('resolved_reports', 0) or 0) / total) * 100, 1) if total else 0,
                    'description_coverage': round(((row.get('with_description', 0) or 0) / total) * 100, 1) if total else 0,
                    'image_coverage': round(((row.get('with_image', 0) or 0) / total) * 100, 1) if total else 0
                })

            return {'success': True, 'period_days': days, 'zones': zones}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_quality_recommendations(self, days=30):
        """Get recommendations to improve report quality."""
        try:
            overview = self.get_quality_overview(days)
            by_type = self.get_report_type_quality(days)
            by_zone = self.get_zone_quality(days)

            if not overview.get('success'):
                return overview

            recommendations = []

            if overview.get('quality_score', 0) < 65:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Data Completeness',
                    'recommendation': f"Quality score is {overview.get('quality_score')} and needs improvement.",
                    'action': 'Make description and location fields mandatory in report submission flow'
                })

            if overview.get('image_coverage', 0) < 40:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Evidence Quality',
                    'recommendation': f"Image coverage is {overview.get('image_coverage')}%.",
                    'action': 'Prompt users to attach photos for faster triage'
                })

            if by_type.get('success'):
                weak_type = next((t for t in by_type.get('types', []) if t.get('resolution_rate', 0) < 50), None)
                if weak_type:
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'category': f"Type {weak_type.get('report_type')}",
                        'recommendation': f"Resolution rate is {weak_type.get('resolution_rate')}%.",
                        'action': 'Introduce type-specific response SOP and escalation paths'
                    })

            if by_zone.get('success'):
                weak_zone = next((z for z in by_zone.get('zones', []) if z.get('resolution_rate', 0) < 50), None)
                if weak_zone:
                    recommendations.append({
                        'priority': 'HIGH',
                        'category': f"Zone {weak_zone.get('zone')}",
                        'recommendation': f"Zone resolution rate is {weak_zone.get('resolution_rate')}% with {weak_zone.get('open_reports')} open reports.",
                        'action': 'Deploy focused closure sprint for this zone'
                    })

            if not recommendations:
                recommendations.append({
                    'priority': 'LOW',
                    'category': 'Performance',
                    'recommendation': 'Report quality indicators are stable for the selected period.',
                    'action': 'Continue weekly review and targeted coaching for field teams'
                })

            return {'success': True, 'recommendations': recommendations, 'recommendation_count': len(recommendations)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
