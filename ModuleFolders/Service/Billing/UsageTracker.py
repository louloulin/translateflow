"""
Usage tracking service integrated with billing system.
"""

import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from ModuleFolders.Infrastructure.Database.pgsql import get_database


class UsageTracker:
    """Track usage for quota enforcement."""

    def __init__(self):
        self.db = get_database()
    
    def record_usage(
        self,
        user_id: str,
        metric_type: str,
        quantity: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a usage event."""
        record_id = str(uuid.uuid4())
        now = datetime.now()

        import json
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO usage_records
               (id, user_id, metric_type, quantity, recorded_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                record_id,
                user_id,
                metric_type,
                quantity,
                now.isoformat(),
                json.dumps(metadata) if metadata else None,
            )
        )

        return {
            "id": record_id,
            "user_id": user_id,
            "metric_type": metric_type,
            "quantity": quantity,
            "recorded_at": now.isoformat(),
        }
    
    def get_today_usage(
        self, user_id: str, metric_type: str = "characters"
    ) -> int:
        """Get today's usage for a user and metric type."""
        today = date.today().isoformat()

        cursor = self.db.cursor()
        cursor.execute(
            """SELECT COALESCE(SUM(quantity), 0) as total
               FROM usage_records
               WHERE user_id = ? AND metric_type = ? AND date(recorded_at) = ?""",
            (user_id, metric_type, today)
        )
        result = cursor.fetchone()

        return result[0] if result else 0

    def get_month_usage(
        self, user_id: str, metric_type: str = "characters"
    ) -> int:
        """Get this month's usage for a user and metric type."""
        today = date.today()
        month_start = date(today.year, today.month, 1).isoformat()

        cursor = self.db.cursor()
        cursor.execute(
            """SELECT COALESCE(SUM(quantity), 0) as total
               FROM usage_records
               WHERE user_id = ? AND metric_type = ? AND date(recorded_at) >= ?""",
            (user_id, metric_type, month_start)
        )
        result = cursor.fetchone()

        return result[0] if result else 0
