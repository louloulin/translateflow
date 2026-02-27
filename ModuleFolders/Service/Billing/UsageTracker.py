"""
Usage tracking service integrated with billing system.
"""

import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from ModuleFolders.Infrastructure.Database.pgsql import get_database


"""
Usage tracking service integrated with billing system.

Tracks user usage across multiple metrics:
- characters: Translation character count
- api_calls: API request count
- storage_mb: Storage usage in MB
- concurrent_tasks: Concurrent task count
- team_members: Team member count
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

from ModuleFolders.Infrastructure.Database.pgsql import get_database


class UsageTracker:
    """Track usage for quota enforcement and analytics."""

    # 支持的指标类型
    METRIC_TYPES = {
        "characters": "翻译字符数",
        "api_calls": "API调用次数",
        "storage_mb": "存储使用(MB)",
        "concurrent_tasks": "并发任务数",
        "team_members": "团队成员数",
    }

    def __init__(self):
        self.db = get_database()

    def record_usage(
        self,
        user_id: str,
        metric_type: str,
        quantity: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        记录一次使用事件

        Args:
            user_id: 用户ID
            metric_type: 指标类型 (characters, api_calls, storage_mb, etc.)
            quantity: 使用量
            metadata: 额外元数据 (task_id, project_id, etc.)

        Returns:
            记录信息字典
        """
        if metric_type not in self.METRIC_TYPES:
            raise ValueError(f"不支持的指标类型: {metric_type}. 支持的类型: {list(self.METRIC_TYPES.keys())}")

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
                json.dumps(metadata, ensure_ascii=False) if metadata else None,
            )
        )
        self.db.commit()

        return {
            "id": record_id,
            "user_id": user_id,
            "metric_type": metric_type,
            "metric_name": self.METRIC_TYPES[metric_type],
            "quantity": quantity,
            "recorded_at": now.isoformat(),
        }

    def get_today_usage(
        self,
        user_id: str,
        metric_type: str = "characters"
    ) -> int:
        """
        获取用户今日使用量

        Args:
            user_id: 用户ID
            metric_type: 指标类型

        Returns:
            今日使用量
        """
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
        self,
        user_id: str,
        metric_type: str = "characters"
    ) -> int:
        """
        获取用户本月使用量

        Args:
            user_id: 用户ID
            metric_type: 指标类型

        Returns:
            本月使用量
        """
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

    def get_usage_history(
        self,
        user_id: str,
        metric_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        """
        获取用户使用历史记录（分页）

        Args:
            user_id: 用户ID
            metric_type: 指标类型过滤 (None 表示全部)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            page: 页码 (从1开始)
            per_page: 每页记录数

        Returns:
            包含历史记录和分页信息的字典
        """
        offset = (page - 1) * per_page

        # 构建查询条件
        conditions = ["user_id = ?"]
        params = [user_id]

        if metric_type:
            conditions.append("metric_type = ?")
            params.append(metric_type)

        if start_date:
            conditions.append("date(recorded_at) >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("date(recorded_at) <= ?")
            params.append(end_date)

        where_clause = " AND ".join(conditions)

        # 查询总数
        cursor = self.db.cursor()
        count_query = f"SELECT COUNT(*) as total FROM usage_records WHERE {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # 查询记录
        params.append(per_page)
        params.append(offset)
        query = f"""
            SELECT id, metric_type, quantity, recorded_at, metadata
            FROM usage_records
            WHERE {where_clause}
            ORDER BY recorded_at DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()

        records = []
        for row in rows:
            import json
            records.append({
                "id": row[0],
                "metric_type": row[1],
                "metric_name": self.METRIC_TYPES.get(row[1], row[1]),
                "quantity": row[2],
                "recorded_at": row[3],
                "metadata": json.loads(row[4]) if row[4] else None,
            })

        total_pages = (total_count + per_page - 1) // per_page

        return {
            "records": records,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }

    def get_daily_usage_stats(
        self,
        user_id: str,
        metric_type: str = "characters",
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        获取每日使用统计（用于趋势图）

        Args:
            user_id: 用户ID
            metric_type: 指标类型
            days: 统计天数

        Returns:
            每日使用量列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)

        cursor = self.db.cursor()
        cursor.execute(
            """SELECT date(recorded_at) as day, COALESCE(SUM(quantity), 0) as total
               FROM usage_records
               WHERE user_id = ? AND metric_type = ?
               AND date(recorded_at) >= ? AND date(recorded_at) <= ?
               GROUP BY date(recorded_at)
               ORDER BY day ASC""",
            (user_id, metric_type, start_date.isoformat(), end_date.isoformat())
        )
        rows = cursor.fetchall()

        # 填充缺失的日期（使用量为0）
        stats = {}
        for row in rows:
            stats[row[0]] = row[1]

        result = []
        current = start_date
        while current <= end_date:
            day_str = current.isoformat()
            result.append({
                "date": day_str,
                "quantity": stats.get(day_str, 0),
            })
            current += timedelta(days=1)

        return result

    def get_usage_summary(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        获取用户使用量汇总（所有指标类型）

        Args:
            user_id: 用户ID

        Returns:
            包含今日、本月、总计使用量的字典
        """
        today = date.today().isoformat()
        month_start = date(today.year, today.month, 1).isoformat()

        cursor = self.db.cursor()

        summary = {
            "today": {},
            "month": {},
            "total": {},
        }

        # 统计每种指标类型
        for metric_type in self.METRIC_TYPES.keys():
            # 今日使用量
            cursor.execute(
                """SELECT COALESCE(SUM(quantity), 0) as total
                   FROM usage_records
                   WHERE user_id = ? AND metric_type = ? AND date(recorded_at) = ?""",
                (user_id, metric_type, today)
            )
            today_usage = cursor.fetchone()[0]
            summary["today"][metric_type] = today_usage

            # 本月使用量
            cursor.execute(
                """SELECT COALESCE(SUM(quantity), 0) as total
                   FROM usage_records
                   WHERE user_id = ? AND metric_type = ? AND date(recorded_at) >= ?""",
                (user_id, metric_type, month_start)
            )
            month_usage = cursor.fetchone()[0]
            summary["month"][metric_type] = month_usage

            # 总使用量
            cursor.execute(
                """SELECT COALESCE(SUM(quantity), 0) as total
                   FROM usage_records
                   WHERE user_id = ? AND metric_type = ?""",
                (user_id, metric_type)
            )
            total_usage = cursor.fetchone()[0]
            summary["total"][metric_type] = total_usage

        return summary

    def get_top_users_by_usage(
        self,
        metric_type: str = "characters",
        days: int = 7,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取使用量最高的用户（管理员功能）

        Args:
            metric_type: 指标类型
            days: 统计天数
            limit: 返回用户数量

        Returns:
            用户使用量排名列表
        """
        start_date = (date.today() - timedelta(days=days)).isoformat()

        cursor = self.db.cursor()
        cursor.execute(
            """SELECT ur.user_id, u.username, u.email, COALESCE(SUM(ur.quantity), 0) as total
               FROM usage_records ur
               LEFT JOIN users u ON ur.user_id = u.id
               WHERE ur.metric_type = ? AND date(ur.recorded_at) >= ?
               GROUP BY ur.user_id
               ORDER BY total DESC
               LIMIT ?""",
            (metric_type, start_date, limit)
        )
        rows = cursor.fetchall()

        return [
            {
                "user_id": row[0],
                "username": row[1],
                "email": row[2],
                "total_usage": row[3],
            }
            for row in rows
        ]

    def delete_old_records(
        self,
        days: int = 180,
    ) -> int:
        """
        删除旧的使用记录（数据清理）

        Args:
            days: 保留天数（超过此天数的记录将被删除）

        Returns:
            删除的记录数
        """
        cutoff_date = (date.today() - timedelta(days=days)).isoformat()

        cursor = self.db.cursor()
        cursor.execute(
            """DELETE FROM usage_records WHERE date(recorded_at) < ?""",
            (cutoff_date,)
        )
        deleted_count = cursor.rowcount
        self.db.commit()

        return deleted_count
