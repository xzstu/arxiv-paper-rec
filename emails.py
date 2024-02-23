"""
some codes ref
- https://www.cnblogs.com/shenh/p/14267345.html
"""

from smtplib import SMTP_SSL
from email.mime.text import MIMEText


def send_email(
    message: str, 
    subject: str, 
    sender_show: str, 
    recipient_show: str, 
    to_addrs: str, 
    cc_show: str = ''
):
    """
    Args:
        message: 邮件内容
        subject: 邮件主题
        sender_show: 发件人显示。建议格式为：`nickname <prefix@domain>`
        recipient_show: 收件人显示，不起实际作用 多个收件人用','隔开如："xxx,xxxx"
        to_addrs: 实际收件人
        cc_show: 抄送人显示，不起实际作用，多个抄送人用','隔开如："xxx,xxxx"
    """

    # 填写真实的发邮件服务器用户名、密码
    user = '884691896@qq.com'
    password = 'xxxx'
    # 邮件内容
    msg = MIMEText(message, 'html', _charset="utf-8")
    # 邮件主题描述
    msg["Subject"] = subject
    # 发件人显示，不起实际作用
    msg["From"] = sender_show
    # 收件人显示，不起实际作用
    msg["To"] = recipient_show
    # 抄送人显示，不起实际作用
    msg["Cc"] = cc_show
    with SMTP_SSL(host="smtp.qq.com",port=465) as smtp:
        # 登录发邮件服务器
        smtp.login(user = user, password = password)
        # 实际发送、接收邮件配置
        smtp.sendmail(from_addr = user, to_addrs=to_addrs.split(','), msg=msg.as_string())
 