"""Waste Classification Insights Service
Provides analytics for waste bin classification, report profiles, and zone-level composition.
"""

from datetime import datetime, timedelta
from models import Database


class WasteClassificationService:
    """Service for analyzing waste classification patterns and operational signals."""

    def __init__(self):
        self.db = Database()

    def _get_connection(self):
        connection = self.db.connect()
        if not connection:
            raise Exception('Unable to connect to database')
        return connection

    def get_classification_summary(self, days=30):
        """Get overall waste classification summary."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_bins,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_bins,
                    SUM(CASE WHEN bin_type = 'general' THEN 1 ELSE 0 END) as general_bins,
                    SUM(CASE WHEN bin_type = 'recyclable' THEN 1 ELSE 0 END) as recyclable_bins,
                    SUM(CASE WHEN bin_type = 'organic' THEN 1 ELSE 0 END) as organic_bins,
                    SUM(CASE WHEN bin_type = 'hazardous' THEN 1 ELSE 0 END) as hazardous_bins
                FROM bins
                """
            )
            bin_stats = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    COUNT(*) as total_reports,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_reports,
                    SUM(CASE WHEN priority IN ('high', 'critical') THEN 1 ELSE 0 END) as high_priority_reports
                FROM waste_reports
                WHERE reported_at >= %s
                """,
                (start_date,)
            )
            report_stats = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT
                    b.bin_type,
                    COUNT(*) as collection_count,
                    AVG(cl.waste_amount) as avg_waste_amount
                FROM collection_logs cl
                JOIN bins b ON cl.bin_id = b.bin_id
                WHERE cl.collection_time >= %s
                GROUP BY b.bin_type
                ORDER BY collection_count DESC
                """,
                (start_date,)
            )
            type_rows = cursor.fetchall()

            collection_breakdown = []
            for row in type_rows:
                collection_breakdown.append({
                    'bin_type': row['bin_type'],
                    'collection_count': row['collection_count'] or 0,
                    'avg_waste_amount': round(row['avg_waste_amount'] or 0, 2)
                })

            total_bins = bin_stats.get('total_bins', 0) or 0
            general_bins = bin_stats.get('general_bins', 0) or 0
            recyclable_bins = bin_stats.get('recyclable_bins', 0) or 0
            organic_bins = bin_stats.get('organic_bins', 0) or 0
            hazardous_bins = bin_stats.get('hazardous_bins', 0) or 0

            dominant_type = 'general'
            type_counts = {
                'general': general_bins,
                'recyclable': recyclable_bins,
                'organic': organic_bins,
                'hazardous': hazardous_bins
            }
            if total_bins > 0:
                dominant_type = max(type_counts, key=type_counts.get)

            return {
                'success': True,
                'period_days': days,
                'total_bins': total_bins,
                'active_bins': bin_stats.get('active_bins', 0) or 0,
                'bin_type_distribution': {
                    'general': general_bins,
                    'recyclable': recyclable_bins,
                    'organic': organic_bins,
                    'hazardous': hazardous_bins
                },
                'dominant_bin_type': dominant_type,
                'waste_reports_last_period': report_stats.get('total_reports', 0) or 0,
                'resolved_reports': report_stats.get('resolved_reports', 0) or 0,
                'high_priority_reports': report_stats.get('high_priority_reports', 0) or 0,
                'collection_breakdown': collection_breakdown
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            try:
                cursor.close()
                connection.close()
            except Exception:
                pass

    def get_type_distribution(self):
        """Get current bin type distribution across the system."""
        try:
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    bin_type,
                    COUNT(*) as bin_count,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count,
                    AVG(waste_level) as avg_fill_level
                FROM bins
                GROUP BY bin_type
                ORDER BY bin_count DESC
                """
            )
            rows = cursor.fetchall()

            total_bins = sum(row['bin_count'] or 0 for row in rows) or 1
            distribution = []
            for row in rows:
                bin_count = row['bin_count'] or 0
                distribution.append({
                    'bin_type': row['bin_type'],
                    'bin_count': bin_count,
                    'active_count': row['active_count'] or 0,
                    'percentage': round((bin_count / total_bins) * 100, 1),
                    'avg_fill_level': round(row['avg_fill_level'] or 0, 1)
                })

            return {
                'success': True,
                'distribution': distribution,
                'total_bins': total_bins
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            try:
                cursor.close()
                connection.close()
            except Exception:
                pass

    def get_zone_classification(self, days=30):
        """Get waste classification by zone."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    b.zone,
                    COUNT(*) as total_bins,
                    SUM(CASE WHEN b.bin_type = 'general' THEN 1 ELSE 0 END) as general_bins,
                    SUM(CASE WHEN b.bin_type = 'recyclable' THEN 1 ELSE 0 END) as recyclable_bins,
                    SUM(CASE WHEN b.bin_type = 'organic' THEN 1 ELSE 0 END) as organic_bins,
                    SUM(CASE WHEN b.bin_type = 'hazardous' THEN 1 ELSE 0 END) as hazardous_bins,
                    AVG(b.waste_level) as avg_fill_level,
                    COUNT(cl.collection_id) as collections_last_period
                FROM bins b
                LEFT JOIN collection_logs cl
                    ON cl.bin_id = b.bin_id
                    AND cl.collection_time >= %s
                WHERE b.zone IS NOT NULL AND b.zone <> ''
                GROUP BY b.zone
                ORDER BY total_bins DESC, b.zone ASC
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            zones = []
            for row in rows:
                type_counts = {
                    'general': row['general_bins'] or 0,
                    'recyclable': row['recyclable_bins'] or 0,
                    'organic': row['organic_bins'] or 0,
                    'hazardous': row['hazardous_bins'] or 0
                }
                dominant_type = max(type_counts, key=type_counts.get) if row['total_bins'] else 'general'
                zones.append({
                    'zone': row['zone'],
                    'total_bins': row['total_bins'] or 0,
                    'dominant_bin_type': dominant_type,
                    'general_bins': type_counts['general'],
                    'recyclable_bins': type_counts['recyclable'],
                    'organic_bins': type_counts['organic'],
                    'hazardous_bins': type_counts['hazardous'],
                    'avg_fill_level': round(row['avg_fill_level'] or 0, 1),
                    'collections_last_period': row['collections_last_period'] or 0
                })

            return {
                'success': True,
                'zones': zones,
                'period_days': days
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            try:
                cursor.close()
                connection.close()
            except Exception:
                pass

    def get_report_profile(self, days=30):
        """Get waste report classification profile."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            connection = self._get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    report_type,
                    COUNT(*) as report_count,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_count,
                    SUM(CASE WHEN priority IN ('high', 'critical') THEN 1 ELSE 0 END) as urgent_count
                FROM waste_reports
                WHERE reported_at >= %s
                GROUP BY report_type
                ORDER BY report_count DESC
                """,
                (start_date,)
            )
            rows = cursor.fetchall()

            reports = []
            for row in rows:
                report_count = row['report_count'] or 0
                resolved_count = row['resolved_count'] or 0
                reports.append({
                    'report_type': row['report_type'],
                    'report_count': report_count,
                    'resolved_count': resolved_count,
                    'urgent_count': row['urgent_count'] or 0,
                    'resolution_rate': round((resolved_count / report_count) * 100, 1) if report_count else 0
                })

            return {
                'success': True,
                'reports': reports,
                'period_days': days
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            try:
                cursor.close()
                connection.close()
            except Exception:
                pass

    def get_classification_recommendations(self, days=30):
        """Generate classification-based recommendations."""
        try:
            summary = self.get_classification_summary(days)
            zones = self.get_zone_classification(days)
            reports = self.get_report_profile(days)

            if not summary.get('success'):
                return summary

            recommendations = []
            distribution = summary.get('bin_type_distribution', {})
            total_bins = max(summary.get('total_bins', 0), 1)
            general_share = (distribution.get('general', 0) / total_bins) * 100
            hazardous_share = (distribution.get('hazardous', 0) / total_bins) * 100
            urgent_reports = summary.get('high_priority_reports', 0)

            if general_share > 45:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Source Separation',
                    'recommendation': f'General-purpose bins represent {general_share:.1f}% of inventory. Expand recyclable and organic separation.',
                    'action': 'Review bin placement and promote source segregation'
                })

            if hazardous_share > 10:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Hazard Control',
                    'recommendation': f'Hazardous bins represent {hazardous_share:.1f}% of inventory. Verify special handling procedures.',
                    'action': 'Inspect hazardous collection routes and safety compliance'
                })

            if urgent_reports > 0:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Incident Response',
                    'recommendation': f'{urgent_reports} high-priority reports were logged in the selected period.',
                    'action': 'Prioritize inspection of bins generating overflow or smell complaints'
                })

            if zones.get('success'):
                for zone in zones.get('zones', [])[:3]:
                    if zone.get('avg_fill_level', 0) >= 75:
                        recommendations.append({
                            'priority': 'MEDIUM',
                            'category': f'Zone {zone.get("zone")}',
                            'recommendation': f'Average fill level is {zone.get("avg_fill_level")}%. Increase collection frequency.',
                            'action': 'Shorten collection cycle in this zone'
                        })

            if reports.get('success'):
                for report in reports.get('reports', []):
                    if report.get('resolution_rate', 0) < 70:
                        recommendations.append({
                            'priority': 'MEDIUM',
                            'category': f'Report Type - {report.get("report_type")}',
                            'recommendation': f'Resolution rate is {report.get("resolution_rate")}%. Improve response workflows.',
                            'action': 'Review escalation and closure process'
                        })
                        break

            return {
                'success': True,
                'recommendations': recommendations,
                'recommendation_count': len(recommendations)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            try:
                cursor.close()
                connection.close()
            except Exception:
                pass
