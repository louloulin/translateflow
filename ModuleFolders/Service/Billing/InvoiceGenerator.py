"""
Invoice generation service.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from ModuleFolders.Infrastructure.Database.pgsql import get_database


class InvoiceGenerator:
    """Generate and manage invoices."""

    def __init__(self):
        self.db = get_database()
    
    def create_invoice(
        self,
        user_id: str,
        amount_due: int,
        currency: str = "cny",
        subscription_id: Optional[str] = None,
        due_days: int = 30,
        stripe_invoice_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new invoice."""
        invoice_id = str(uuid.uuid4())
        now = datetime.now()
        due_date = now + timedelta(days=due_days)
        
        cursor = self.db.cursor()
        cursor.execute(
            """INSERT INTO invoices
               (id, user_id, subscription_id, stripe_invoice_id, amount_due,
                amount_paid, currency, status, due_date, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                invoice_id,
                user_id,
                subscription_id,
                stripe_invoice_id,
                amount_due,
                0,
                currency,
                "pending",
                due_date.isoformat(),
                now.isoformat(),
            )
        )
        
        return {
            "id": invoice_id,
            "user_id": user_id,
            "amount_due": amount_due,
            "currency": currency,
            "status": "pending",
            "due_date": due_date.isoformat(),
            "created_at": now.isoformat(),
        }
    
    def get_user_invoices(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get invoices for a user."""
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT * FROM invoices
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ? OFFSET ?""",
            (user_id, limit, offset)
        )
        rows = cursor.fetchall()

        return [self._row_to_dict(row) for row in rows]
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        return {
            "id": row[0],
            "user_id": row[1],
            "subscription_id": row[2],
            "stripe_invoice_id": row[3],
            "amount_due": row[4],
            "amount_paid": row[5],
            "currency": row[6],
            "status": row[7],
            "invoice_pdf": row[8],
            "due_date": row[9],
            "paid_at": row[10],
            "created_at": row[11],
        }
