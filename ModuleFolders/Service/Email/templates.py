"""
Email template definitions.

Provides HTML and plain text templates for various email types.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class EmailTemplate:
    """Email template with HTML and text versions."""
    subject: str
    html: str
    text: str


def _render_base_html(title: str, content: str) -> str:
    """Render base HTML template with styling."""
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #4F46E5;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #4F46E5;
        }}
        .content {{
            margin: 30px 0;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background-color: #4F46E5;
            color: #ffffff;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            font-size: 14px;
            color: #666;
        }}
        .code {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            text-align: center;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">TranslateFlow</div>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>此邮件由系统自动发送，请勿直接回复。</p>
            <p>&copy; 2025 TranslateFlow. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""


def get_verification_email_template(username: str, verification_url: str) -> EmailTemplate:
    """Get email verification template."""
    html_content = f"""
        <h2>欢迎来到 TranslateFlow!</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>感谢您注册 TranslateFlow。请点击下方按钮验证您的邮箱地址：</p>
        <p><a href="{verification_url}" class="button">验证邮箱</a></p>
        <p>如果按钮无法点击，请复制以下链接到浏览器地址栏：</p>
        <p class="code">{verification_url}</p>
        <p>此验证链接将在 24 小时后过期。</p>
    """

    text_content = f"""欢迎来到 TranslateFlow!

你好 {username},

感谢您注册 TranslateFlow。请访问以下链接验证您的邮箱地址：

{verification_url}

此验证链接将在 24 小时后过期。

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject="验证您的 TranslateFlow 邮箱地址",
        html=_render_base_html("验证邮箱", html_content),
        text=text_content
    )


def get_password_reset_email_template(username: str, reset_url: str) -> EmailTemplate:
    """Get password reset template."""
    html_content = f"""
        <h2>重置您的密码</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>我们收到了您的密码重置请求。请点击下方按钮重置密码：</p>
        <p><a href="{reset_url}" class="button">重置密码</a></p>
        <p>如果按钮无法点击，请复制以下链接到浏览器地址栏：</p>
        <p class="code">{reset_url}</p>
        <p>此重置链接将在 1 小时后过期。</p>
        <p><strong>如果您没有请求重置密码，请忽略此邮件。</strong></p>
    """

    text_content = f"""重置您的密码

你好 {username},

我们收到了您的密码重置请求。请访问以下链接重置密码：

{reset_url}

此重置链接将在 1 小时后过期。

如果您没有请求重置密码，请忽略此邮件。

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject="重置您的 TranslateFlow 密码",
        html=_render_base_html("重置密码", html_content),
        text=text_content
    )


def get_welcome_email_template(username: str) -> EmailTemplate:
    """Get welcome email template."""
    html_content = f"""
        <h2>欢迎加入 TranslateFlow!</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>感谢您注册 TranslateFlow！您的邮箱已成功验证。</p>
        <h3>开始使用</h3>
        <ul>
            <li>支持 18+ AI 翻译平台</li>
            <li>支持 25+ 文件格式</li>
            <li>智能术语表管理</li>
            <li>批量翻译处理</li>
        </ul>
        <p>立即开始您的翻译之旅！</p>
        <p><a href="https://translateflow.example.com/dashboard" class="button">前往控制台</a></p>
    """

    text_content = f"""欢迎加入 TranslateFlow!

你好 {username},

感谢您注册 TranslateFlow！您的邮箱已成功验证。

开始使用：
- 支持 18+ AI 翻译平台
- 支持 25+ 文件格式
- 智能术语表管理
- 批量翻译处理

立即开始您的翻译之旅！
https://translateflow.example.com/dashboard

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject="欢迎来到 TranslateFlow!",
        html=_render_base_html("欢迎", html_content),
        text=text_content
    )


def get_subscription_confirmation_template(
    username: str,
    plan_name: str,
    amount: str
) -> EmailTemplate:
    """Get subscription confirmation template."""
    html_content = f"""
        <h2>订阅确认</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>恭喜！您已成功订阅 <strong>{plan_name}</strong> 计划。</p>
        <h3>订阅详情</h3>
        <ul>
            <li>计划：{plan_name}</li>
            <li>费用：{amount}/月</li>
        </ul>
        <p>您可以随时在账户设置中管理或取消订阅。</p>
        <p><a href="https://translateflow.example.com/settings/billing" class="button">管理订阅</a></p>
    """

    text_content = f"""订阅确认

你好 {username},

恭喜！您已成功订阅 {plan_name} 计划。

订阅详情：
- 计划：{plan_name}
- 费用：{amount}/月

您可以随时在账户设置中管理或取消订阅。
https://translateflow.example.com/settings/billing

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject=f"TranslateFlow 订阅确认 - {plan_name}",
        html=_render_base_html("订阅确认", html_content),
        text=text_content
    )


def get_quota_warning_template(
    username: str,
    plan_name: str,
    used_percentage: int
) -> EmailTemplate:
    """Get quota warning template."""
    html_content = f"""
        <h2>配额使用提醒</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>您的 <strong>{plan_name}</strong> 计划配额已使用 <strong>{used_percentage}%</strong>。</p>
        <p>当配额用尽后，翻译功能将暂时不可用。</p>
        <p>建议升级到更高等级的计划以获得更多配额。</p>
        <p><a href="https://translateflow.example.com/settings/billing" class="button">查看计划</a></p>
    """

    text_content = f"""配额使用提醒

你好 {username},

您的 {plan_name} 计划配额已使用 {used_percentage}%。

当配额用尽后，翻译功能将暂时不可用。

建议升级到更高等级的计划以获得更多配额。
https://translateflow.example.com/settings/billing

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject=f"TranslateFlow 配额使用提醒 - {used_percentage}%",
        html=_render_base_html("配额提醒", html_content),
        text=text_content
    )


def get_login_alert_template(
    username: str,
    ip_address: str,
    location: str = None,
    time: str = None
) -> EmailTemplate:
    """Get login alert template for security notifications."""
    location_str = f" ({location})" if location else ""
    time_str = time if time else "最近"

    html_content = f"""
        <h2>登录安全提醒</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>我们检测到您的账户在{time_str}有新的登录活动：</p>
        <ul>
            <li>IP 地址：{ip_address}</li>
            <li>位置：{ip_address}{location_str}</li>
        </ul>
        <p>如果这是您本人的操作，请忽略此邮件。</p>
        <p><strong>如果这不是您本人的操作，请立即修改密码并联系支持团队。</strong></p>
        <p><a href="https://translateflow.example.com/settings/security" class="button">查看安全设置</a></p>
    """

    text_content = f"""登录安全提醒

你好 {username},

我们检测到您的账户在{time_str}有新的登录活动：

- IP 地址：{ip_address}
- 位置：{ip_address}{location_str}

如果这是您本人的操作，请忽略此邮件。

如果这不是您本人的操作，请立即修改密码并联系支持团队。
https://translateflow.example.com/settings/security

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject="TranslateFlow 登录安全提醒",
        html=_render_base_html("安全提醒", html_content),
        text=text_content
    )
