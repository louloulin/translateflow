"""
Invoice generation service with PDF support.
"""

import uuid
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ModuleFolders.Infrastructure.Database.pgsql import get_database


class InvoiceGenerator:
    """Generate and manage invoices with PDF support."""

    def __init__(self):
        self.db = get_database()
        self._init_fonts()
        self.pdf_output_dir = Path("invoices")
        self.pdf_output_dir.mkdir(exist_ok=True)

    def _init_fonts(self):
        """初始化中文字体支持。

        尝试注册系统中可用的中文字体，用于发票PDF生成。
        """
        try:
            # 尝试注册常见的中文字体
            font_paths = [
                # macOS 系统字体
                "/System/Library/Fonts/PingFang.ttc",  # 苹方
                "/System/Library/Fonts/STHeiti Light.ttc",  # 黑体
                "/System/Library/Fonts/STSong.ttf",  # 宋体
                # Linux 系统字体
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # 文泉驿正黑
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                # Windows 系统字体
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        # 注册字体（使用中文名称）
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        self.chinese_font = 'ChineseFont'
                        return
                    except Exception:
                        continue

            # 如果没有找到系统字体，使用默认字体（中文可能显示为方块）
            self.chinese_font = 'Helvetica'
        except Exception:
            self.chinese_font = 'Helvetica'

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

    def generate_pdf(
        self,
        invoice_id: str,
        output_path: Optional[str] = None,
        company_info: Optional[Dict[str, str]] = None,
    ) -> str:
        """生成发票 PDF 文件。

        Args:
            invoice_id: 发票ID
            output_path: 输出文件路径（可选，默认为 invoices/{invoice_id}.pdf）
            company_info: 公司信息（可选）

        Returns:
            生成的PDF文件路径

        Raises:
            ValueError: 发票不存在
            Exception: PDF生成失败
        """
        # 获取发票信息
        invoice_data = self._get_invoice_details(invoice_id)
        if not invoice_data:
            raise ValueError(f"发票不存在: {invoice_id}")

        # 默认公司信息
        default_company_info = {
            "name": "TranslateFlow",
            "address": "中国",
            "phone": "+86 400-000-0000",
            "email": "billing@translateflow.com",
            "website": "https://translateflow.com",
        }
        company_info = company_info or default_company_info

        # 生成 PDF
        if output_path is None:
            output_path = str(self.pdf_output_dir / f"{invoice_id}.pdf")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )

        # 构建发票内容
        story = []
        styles = getSampleStyleSheet()

        # 自定义样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=self.chinese_font,
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=self.chinese_font,
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=self.chinese_font,
            fontSize=10,
            textColor=colors.HexColor('#666666'),
        )

        # 标题
        title = Paragraph("发票", title_style)
        story.append(title)
        story.append(Spacer(1, 0.5*cm))

        # 发票信息表格
        invoice_info = [
            ["发票编号:", invoice_data['id']],
            ["创建日期:", invoice_data['created_at'][:10]],
            ["到期日期:", invoice_data['due_date'][:10]],
            ["状态:", self._translate_status(invoice_data['status'])],
        ]

        invoice_table = Table(invoice_info, colWidths=[4*cm, 8*cm])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        story.append(invoice_table)
        story.append(Spacer(1, 1*cm))

        # 客户信息
        story.append(Paragraph("客户信息", heading_style))
        customer_info = [
            ["用户ID:", invoice_data['user_id']],
            ["邮箱:", invoice_data.get('email', 'N/A')],
        ]

        customer_table = Table(customer_info, colWidths=[4*cm, 8*cm])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#666666')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
        ]))
        story.append(customer_table)
        story.append(Spacer(1, 1*cm))

        # 发票明细
        story.append(Paragraph("发票明细", heading_style))

        # 计算金额
        amount_due = invoice_data['amount_due'] / 100  # 转换为元
        amount_paid = invoice_data['amount_paid'] / 100
        currency_symbol = self._get_currency_symbol(invoice_data['currency'])

        items = [
            ["项目", "描述", "数量", "单价", "金额"],
            [
                "订阅服务",
                self._get_plan_description(invoice_data.get('subscription_id')),
                "1",
                f"{currency_symbol}{amount_due:.2f}",
                f"{currency_symbol}{amount_due:.2f}",
            ],
        ]

        items_table = Table(items, colWidths=[4*cm, 6*cm, 2*cm, 3*cm, 3*cm])
        items_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (1, 0), (-1, -1), colors.HexColor('#666666')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 1*cm))

        # 总计
        total = [
            ["", "", "", "小计:", f"{currency_symbol}{amount_due:.2f}"],
            ["", "", "", "已付:", f"{currency_symbol}{amount_paid:.2f}"],
            ["", "", "", "应付余额:", f"{currency_symbol}{(amount_due - amount_paid):.2f}"],
        ]

        total_table = Table(total, colWidths=[4*cm, 6*cm, 2*cm, 3*cm, 3*cm])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -2), colors.HexColor('#666666')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1a1a1a')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            ('BACKGROUND', (3, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ]))
        story.append(total_table)
        story.append(Spacer(1, 2*cm))

        # 公司信息
        story.append(Paragraph("公司信息", heading_style))
        company_text = f"""
        {company_info['name']}<br/>
        地址: {company_info['address']}<br/>
        电话: {company_info['phone']}<br/>
        邮箱: {company_info['email']}<br/>
        网站: {company_info['website']}
        """
        company_paragraph = Paragraph(company_text.strip(), normal_style)
        story.append(company_paragraph)
        story.append(Spacer(1, 1*cm))

        # 备注
        if invoice_data['status'] == 'pending':
            note = Paragraph(
                "<b>备注:</b> 请在到期日期前完成支付。",
                ParagraphStyle('Note', parent=normal_style, fontName=self.chinese_font)
            )
            story.append(note)

        # 生成 PDF
        try:
            doc.build(story)
            return output_path
        except Exception as e:
            raise Exception(f"PDF生成失败: {str(e)}")

    def generate_pdf_bytes(
        self,
        invoice_id: str,
        company_info: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """生成发票 PDF 字节数据。

        Args:
            invoice_id: 发票ID
            company_info: 公司信息（可选）

        Returns:
            PDF文件的字节数据

        Raises:
            ValueError: 发票不存在
            Exception: PDF生成失败
        """
        from io import BytesIO

        # 生成到内存
        buffer = BytesIO()
        temp_path = str(self.pdf_output_dir / f"temp_{invoice_id}.pdf")

        try:
            # 先生成到文件
            self.generate_pdf(invoice_id, temp_path, company_info)

            # 读取文件内容
            with open(temp_path, 'rb') as f:
                pdf_data = f.read()

            return pdf_data
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _get_invoice_details(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """获取发票详细信息。

        Args:
            invoice_id: 发票ID

        Returns:
            发票详细信息字典，如果不存在则返回 None
        """
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT i.*, u.email
               FROM invoices i
               LEFT JOIN users u ON i.user_id = u.id
               WHERE i.id = ?""",
            (invoice_id,)
        )
        row = cursor.fetchone()

        if not row:
            return None

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
            "email": row[12] if len(row) > 12 else None,
        }

    def _translate_status(self, status: str) -> str:
        """翻译发票状态为中文。

        Args:
            status: 英文状态

        Returns:
            中文状态
        """
        status_map = {
            "pending": "待支付",
            "paid": "已支付",
            "cancelled": "已取消",
            "failed": "支付失败",
        }
        return status_map.get(status, status)

    def _get_currency_symbol(self, currency: str) -> str:
        """获取货币符号。

        Args:
            currency: 货币代码

        Returns:
            货币符号
        """
        currency_symbols = {
            "cny": "¥",
            "usd": "$",
            "eur": "€",
            "jpy": "¥",
        }
        return currency_symbols.get(currency.lower(), currency.upper())

    def _get_plan_description(self, subscription_id: Optional[str]) -> str:
        """获取订阅计划描述。

        Args:
            subscription_id: 订阅ID

        Returns:
            计划描述
        """
        if not subscription_id:
            return "按量计费服务"

        # 从数据库获取订阅信息
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT plan FROM tenants WHERE id = (SELECT tenant_id FROM subscriptions WHERE id = ?)",
            (subscription_id,)
        )
        row = cursor.fetchone()

        if row:
            plan_names = {
                "free": "免费计划",
                "starter": "入门计划",
                "pro": "专业计划",
                "enterprise": "企业计划",
            }
            return plan_names.get(row[0], row[0].capitalize())

        return "订阅服务"
