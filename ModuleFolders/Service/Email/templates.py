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


def get_email_change_notification_template(username: str) -> EmailTemplate:
    """Get email change notification template."""
    html_content = f"""
        <h2>邮箱地址已更改</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>您的账户邮箱地址已成功更改。</p>
        <p>为了安全起见，您需要重新验证新的邮箱地址。</p>
        <p>如果这不是您本人的操作，请立即联系支持团队。</p>
        <p><a href="https://translateflow.example.com/settings/security" class="button">查看安全设置</a></p>
    """

    text_content = f"""邮箱地址已更改

你好 {username},

您的账户邮箱地址已成功更改。

为了安全起见，您需要重新验证新的邮箱地址。

如果这不是您本人的操作，请立即联系支持团队。
https://translateflow.example.com/settings/security

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject="TranslateFlow 邮箱地址已更改",
        html=_render_base_html("邮箱更改", html_content),
        text=text_content
    )


def get_password_change_notification_template(username: str) -> EmailTemplate:
    """Get password change notification template."""
    html_content = f"""
        <h2>密码已更改</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>您的账户密码已成功更改。</p>
        <p>所有设备上的登录会话已被撤销，需要重新登录。</p>
        <p>如果这不是您本人的操作，请立即联系支持团队。</p>
        <p><a href="https://translateflow.example.com/settings/security" class="button">查看安全设置</a></p>
    """

    text_content = f"""密码已更改

你好 {username},

您的账户密码已成功更改。

所有设备上的登录会话已被撤销，需要重新登录。

如果这不是您本人的操作，请立即联系支持团队。
https://translateflow.example.com/settings/security

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject="TranslateFlow 密码已更改",
        html=_render_base_html("密码更改", html_content),
        text=text_content
    )


def get_account_deletion_notification_template(username: str) -> EmailTemplate:
    """Get account deletion notification template."""
    html_content = f"""
        <h2>账户已删除</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>您的 TranslateFlow 账户已被成功删除。</p>
        <p>您的所有个人数据已被永久删除，无法恢复。</p>
        <p>感谢您使用 TranslateFlow。我们希望未来能再次为您服务。</p>
    """

    text_content = f"""账户已删除

你好 {username},

您的 TranslateFlow 账户已被成功删除。

您的所有个人数据已被永久删除，无法恢复。

感谢您使用 TranslateFlow。我们希望未来能再次为您服务。

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject="TranslateFlow 账户已删除",
        html=_render_base_html("账户删除", html_content),
        text=text_content
    )


def get_role_change_notification_template(username: str, new_role: str) -> EmailTemplate:
    """Get role change notification template."""
    role_names = {
        "super_admin": "超级管理员",
        "tenant_admin": "租户管理员",
        "team_admin": "团队管理员",
        "translation_admin": "翻译管理员",
        "developer": "开发者",
        "user": "普通用户",
    }
    role_name = role_names.get(new_role, new_role)

    html_content = f"""
        <h2>用户角色已更改</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>您的账户角色已更改为 <strong>{role_name}</strong>。</p>
        <p>新角色的权限已立即生效。</p>
        <p>如有任何疑问，请联系管理员。</p>
    """

    text_content = f"""用户角色已更改

你好 {username},

您的账户角色已更改为 {role_name}。

新角色的权限已立即生效。

如有任何疑问，请联系管理员。

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject="TranslateFlow 用户角色已更改",
        html=_render_base_html("角色更改", html_content),
        text=text_content
    )


def get_account_suspended_notification_template(username: str, reason: str) -> EmailTemplate:
    """Get account suspended notification template."""
    html_content = f"""
        <h2>账户已被暂停</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>您的 TranslateFlow 账户已被暂停。</p>
        <p><strong>原因：</strong>{reason}</p>
        <p>在账户暂停期间，您将无法访问大部分功能。</p>
        <p>如有任何疑问或希望重新激活账户，请联系支持团队。</p>
        <p><a href="mailto:support@translateflow.example.com" class="button">联系支持</a></p>
    """

    text_content = f"""账户已被暂停

你好 {username},

您的 TranslateFlow 账户已被暂停。

原因：{reason}

在账户暂停期间，您将无法访问大部分功能。

如有任何疑问或希望重新激活账户，请联系支持团队。
support@translateflow.example.com

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject="TranslateFlow 账户已被暂停",
        html=_render_base_html("账户暂停", html_content),
        text=text_content
    )


def get_account_reactivated_notification_template(username: str) -> EmailTemplate:
    """Get account reactivated notification template."""
    html_content = f"""
        <h2>账户已重新激活</h2>
        <p>你好 <strong>{username}</strong>,</p>
        <p>您的 TranslateFlow 账户已被重新激活。</p>
        <p>您现在可以正常使用所有功能。</p>
        <p>如有任何疑问，请联系支持团队。</p>
        <p><a href="https://translateflow.example.com/dashboard" class="button">前往控制台</a></p>
    """

    text_content = f"""账户已重新激活

你好 {username},

您的 TranslateFlow 账户已被重新激活。

您现在可以正常使用所有功能。

如有任何疑问，请联系支持团队。
https://translateflow.example.com/dashboard

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject="TranslateFlow 账户已重新激活",
        html=_render_base_html("账户激活", html_content),
        text=text_content
    )


def get_payment_notification_template(
    username: str,
    payment_id: str,
    amount: float,
    currency: str,
    status: str,
    error_message: str = None
) -> EmailTemplate:
    """获取支付通知模板"""
    if status == "成功":
        html_content = f"""
            <h2>支付成功通知</h2>
            <p>你好 <strong>{username}</strong>,</p>
            <p>您的支付已成功处理！</p>
            <h3>支付详情</h3>
            <ul>
                <li>支付ID：{payment_id}</li>
                <li>金额：{currency} {amount:.2f}</li>
                <li>状态：成功</li>
            </ul>
            <p>感谢您的付款！</p>
        """

        text_content = f"""支付成功通知

你好 {username},

您的支付已成功处理！

支付详情：
- 支付ID：{payment_id}
- 金额：{currency} {amount:.2f}
- 状态：成功

感谢您的付款！

---
TranslateFlow - AI驱动的翻译工具
"""

        return EmailTemplate(
            subject="TranslateFlow 支付成功",
            html=_render_base_html("支付成功", html_content),
            text=text_content
        )
    else:
        html_content = f"""
            <h2>支付失败通知</h2>
            <p>你好 <strong>{username}</strong>,</p>
            <p>很抱歉，您的支付未能成功处理。</p>
            <h3>支付详情</h3>
            <ul>
                <li>支付ID：{payment_id}</li>
                <li>状态：失败</li>
            </ul>
            <p><strong>失败原因：</strong>{error_message or '未知错误'}</p>
            <p>请检查您的支付方式或尝试其他支付方式。</p>
            <p><a href="https://translateflow.example.com/settings/billing" class="button">管理账单</a></p>
        """

        text_content = f"""支付失败通知

你好 {username},

很抱歉，您的支付未能成功处理。

支付详情：
- 支付ID：{payment_id}
- 状态：失败

失败原因：{error_message or '未知错误'}

请检查您的支付方式或尝试其他支付方式。
https://translateflow.example.com/settings/billing

---
TranslateFlow - AI驱动的翻译工具
"""

        return EmailTemplate(
            subject="TranslateFlow 支付失败",
            html=_render_base_html("支付失败", html_content),
            text=text_content
        )


def get_subscription_notification_template(
    username: str,
    event: str,
    plan: str,
    status: str = None
) -> EmailTemplate:
    """获取订阅通知模板"""
    plan_names = {
        "free": "免费计划",
        "starter": "入门计划",
        "pro": "专业计划",
        "enterprise": "企业计划",
    }
    plan_name = plan_names.get(plan, plan)

    if event == "updated":
        html_content = f"""
            <h2>订阅已更新</h2>
            <p>你好 <strong>{username}</strong>,</p>
            <p>您的订阅计划已更新为 <strong>{plan_name}</strong>。</p>
            <p>状态：{status or '活跃'}</p>
            <p>新计划的功能已立即生效。</p>
            <p><a href="https://translateflow.example.com/settings/billing" class="button">管理订阅</a></p>
        """

        text_content = f"""订阅已更新

你好 {username},

您的订阅计划已更新为 {plan_name}。

状态：{status or '活跃'}

新计划的功能已立即生效。
https://translateflow.example.com/settings/billing

---
TranslateFlow - AI驱动的翻译工具
"""

        return EmailTemplate(
            subject="TranslateFlow 订阅已更新",
            html=_render_base_html("订阅更新", html_content),
            text=text_content
        )
    elif event == "cancelled":
        html_content = f"""
            <h2>订阅已取消</h2>
            <p>你好 <strong>{username}</strong>,</p>
            <p>您的订阅已被取消。</p>
            <p>您的账户已降级为免费计划。</p>
            <p>感谢您使用 TranslateFlow。我们希望未来能再次为您服务。</p>
            <p><a href="https://translateflow.example.com/settings/billing" class="button">查看计划</a></p>
        """

        text_content = f"""订阅已取消

你好 {username},

您的订阅已被取消。

您的账户已降级为免费计划。

感谢您使用 TranslateFlow。我们希望未来能再次为您服务。
https://translateflow.example.com/settings/billing

---
TranslateFlow - AI驱动的翻译工具
"""

        return EmailTemplate(
            subject="TranslateFlow 订阅已取消",
            html=_render_base_html("订阅取消", html_content),
            text=text_content
        )

    return EmailTemplate(
        subject="TranslateFlow 订阅通知",
        html=_render_base_html("订阅通知", "<p>您的订阅状态已变更。</p>"),
        text="您的订阅状态已变更。"
    )


def get_invoice_notification_template(
    username: str,
    invoice_id: str,
    status: str,
    amount: float = None,
    currency: str = None,
    attempt_count: int = None
) -> EmailTemplate:
    """获取发票通知模板"""
    if status == "已支付":
        html_content = f"""
            <h2>发票已支付</h2>
            <p>你好 <strong>{username}</strong>,</p>
            <p>您的发票已成功支付。</p>
            <h3>发票详情</h3>
            <ul>
                <li>发票ID：{invoice_id}</li>
                <li>金额：{currency} {amount:.2f if amount else '0.00'}</li>
                <li>状态：已支付</li>
            </ul>
            <p>您可以在账单页面查看和下载发票。</p>
            <p><a href="https://translateflow.example.com/settings/billing" class="button">查看发票</a></p>
        """

        text_content = f"""发票已支付

你好 {username},

您的发票已成功支付。

发票详情：
- 发票ID：{invoice_id}
- 金额：{currency} {amount:.2f if amount else '0.00'}
- 状态：已支付

您可以在账单页面查看和下载发票。
https://translateflow.example.com/settings/billing

---
TranslateFlow - AI驱动的翻译工具
"""

        return EmailTemplate(
            subject="TranslateFlow 发票已支付",
            html=_render_base_html("发票支付", html_content),
            text=text_content
        )
    elif status == "支付失败":
        html_content = f"""
            <h2>发票支付失败</h2>
            <p>你好 <strong>{username}</strong>,</p>
            <p>很抱歉，您的发票支付未能成功处理。</p>
            <h3>发票详情</h3>
            <ul>
                <li>发票ID：{invoice_id}</li>
                <li>尝试次数：{attempt_count or 1}</li>
                <li>状态：支付失败</li>
            </ul>
            <p>请检查您的支付方式或更新付款信息。</p>
            <p>我们将在接下来的几天内重试扣款。</p>
            <p><a href="https://translateflow.example.com/settings/billing" class="button">更新支付方式</a></p>
        """

        text_content = f"""发票支付失败

你好 {username},

很抱歉，您的发票支付未能成功处理。

发票详情：
- 发票ID：{invoice_id}
- 尝试次数：{attempt_count or 1}
- 状态：支付失败

请检查您的支付方式或更新付款信息。

我们将在接下来的几天内重试扣款。
https://translateflow.example.com/settings/billing

---
TranslateFlow - AI驱动的翻译工具
"""

        return EmailTemplate(
            subject="TranslateFlow 发票支付失败",
            html=_render_base_html("发票支付失败", html_content),
            text=text_content
        )

    return EmailTemplate(
        subject="TranslateFlow 发票通知",
        html=_render_base_html("发票通知", "<p>您有一张新的发票。</p>"),
        text="您有一张新的发票。"
    )


def get_team_invitation_template(
    invitee_name: str,
    inviter_name: str,
    team_name: str,
    invitation_url: str,
    role: str = "member"
) -> EmailTemplate:
    """获取团队邀请邮件模板"""
    role_names = {
        "owner": "所有者",
        "admin": "管理员",
        "member": "成员",
    }
    role_name = role_names.get(role, "成员")
    
    html_content = f"""
        <h2>团队邀请</h2>
        <p>你好 <strong>{invitee_name}</strong>,</p>
        <p><strong>{inviter_name}</strong> 邀请您加入团队 <strong>{team_name}</strong>。</p>
        <h3>邀请详情</h3>
        <ul>
            <li>团队：{team_name}</li>
            <li>邀请人：{inviter_name}</li>
            <li>角色：{role_name}</li>
        </ul>
        <p>点击下方按钮接受邀请：</p>
        <p><a href="{invitation_url}" class="button">接受邀请</a></p>
        <p>如果按钮无法点击，请复制以下链接到浏览器地址栏：</p>
        <p class="code">{invitation_url}</p>
        <p>此邀请链接将在 7 天后过期。</p>
        <p>如果这不是您期望的邀请，请忽略此邮件。</p>
    """

    text_content = f"""团队邀请

你好 {invitee_name},

{inviter_name} 邀请您加入团队 {team_name}。

邀请详情：
- 团队：{team_name}
- 邀请人：{inviter_name}
- 角色：{role_name}

点击下方链接接受邀请：
{invitation_url}

此邀请链接将在 7 天后过期。

如果这不是您期望的邀请，请忽略此邮件。

---
TranslateFlow - AI驱动的翻译工具
"""

    return EmailTemplate(
        subject=f"TranslateFlow 团队邀请 - {team_name}",
        html=_render_base_html("团队邀请", html_content),
        text=text_content
    )
