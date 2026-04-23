"""
Email Sender for Daily Sales Briefing (Community Edition)

╔══════════════════════════════════════════════════════════════════════════╗
║                       COMMUNITY EDITION NOTICE                           ║
║                                                                          ║
║  This version sends a basic email with PDF attachment.                   ║
║                                                                          ║
║  The Pro edition adds:                                                   ║
║    - Rich HTML email body with insights summary                          ║
║    - Customizable email templates per business                           ║
║    - Exponential-backoff retry with multiple SMTP fallbacks              ║
║    - SMS / WhatsApp delivery (via Twilio)                                ║
║    - Slack channel delivery                                              ║
║    - Delivery receipt tracking                                           ║
║                                                                          ║
║  Contact: razeghi.a@gmail.com for commercial licensing.                  ║
╚══════════════════════════════════════════════════════════════════════════╝

SECURITY: Credentials can be provided via environment variables:
  BRIEFING_SMTP_EMAIL
  BRIEFING_SMTP_PASSWORD  (Gmail App Password)

Environment variables override config file values.
"""

import smtplib
import ssl
import os
import logging
from email.message import EmailMessage
from email.utils import formatdate
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSender:
    """Handles sending the briefing report via email."""
    
    def __init__(self, smtp_server, smtp_port, sender_email, sender_password, 
                 use_tls=True):
        """
        Initialize the email sender.
        
        Parameters:
        -----------
        smtp_server : str
            SMTP server address (e.g., 'smtp.gmail.com')
        smtp_port : int
            SMTP port (587 for TLS, 465 for SSL)
        sender_email : str
            The sender's email address
        sender_password : str
            App password (not regular password for Gmail)
        use_tls : bool
            Whether to use TLS (True) or SSL (False)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls
    
    def send_report(self, recipient_email, business_name, pdf_path, 
                    summary_stats=None, alerts=None, max_retries=1):
        """
        Send the briefing report with PDF attachment.
        
        [COMMUNITY EDITION] Retries once on transient failures.
        [PRO EDITION] Exponential backoff with up to 5 retries, plus fallback
        to secondary SMTP server.
        
        Parameters:
        -----------
        recipient_email : str
        business_name : str
        pdf_path : str
        summary_stats : dict, optional
        alerts : list, optional
        max_retries : int
            How many times to retry on failure (default: 1 for community)
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF report not found: {pdf_path}")
        
        msg = self._build_message(
            recipient_email, business_name, pdf_path, summary_stats, alerts
        )
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                self._send_via_smtp(msg)
                if attempt > 0:
                    logger.info(f"Email sent successfully on retry {attempt}")
                return True
            except (smtplib.SMTPException, ConnectionError, TimeoutError) as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(
                        f"Email send failed (attempt {attempt + 1}): {e}. Retrying..."
                    )
                else:
                    logger.error(f"Email send failed after {max_retries + 1} attempts: {e}")
        
        raise last_error
    
    def _build_message(self, recipient_email, business_name, pdf_path,
                       summary_stats, alerts):
        """Build the email message with PDF attachment."""
        msg = EmailMessage()
        today = datetime.now().strftime('%A, %B %d, %Y')
        msg['Subject'] = f"Daily Sales Briefing — {business_name} — {today}"
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Date'] = formatdate(localtime=True)
        
        text_body = self._build_text_body(business_name, today, summary_stats, alerts)
        msg.set_content(text_body)
        
        html_body = self._build_html_body(business_name, today, summary_stats, alerts)
        msg.add_alternative(html_body, subtype='html')
        
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        pdf_filename = os.path.basename(pdf_path)
        msg.add_attachment(
            pdf_data, maintype='application', subtype='pdf', filename=pdf_filename
        )
        return msg
    
    def _send_via_smtp(self, msg):
        """Send a prepared message via SMTP."""
        context = ssl.create_default_context()
        
        if self.use_tls:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, 
                                   context=context, timeout=30) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
    
    def _build_text_body(self, business_name, date_str, summary_stats, alerts):
        """Build plain-text email body as fallback."""
        lines = [
            f"Good morning,",
            f"",
            f"Your Daily Sales Briefing for {business_name} is ready.",
            f"Date: {date_str}",
            f"",
        ]
        
        if summary_stats:
            lines.extend([
                f"Quick Summary:",
                f"  Revenue:      ${summary_stats['total_revenue']:,.2f}",
                f"  Orders:       {summary_stats['total_orders']}",
                f"  Avg Order:    ${summary_stats['avg_order_value']:.2f}",
                f"",
            ])
        
        if alerts:
            lines.append("Alerts:")
            for alert in alerts:
                symbol = "[+]" if alert['type'] == 'positive' else "[!]"
                lines.append(f"  {symbol} {alert['title']}: {alert['message']}")
            lines.append("")
        
        lines.extend([
            f"The full report is attached as a PDF.",
            f"",
            f"--",
            f"Daily Sales Briefing",
            f"Automated report delivery",
        ])
        
        return "\n".join(lines)
    
    def _build_html_body(self, business_name, date_str, summary_stats, alerts):
        """
        Build HTML email body.
        
        [COMMUNITY EDITION] Basic HTML body with summary table.
        [PRO EDITION] Rich HTML with inline charts, insights summary,
        customer branding, and mobile-optimized layout.
        """
        stats_html = ""
        if summary_stats:
            stats_html = f"""
            <h3 style="color:#212529;margin-top:24px;">Quick Summary</h3>
            <table cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;">
              <tr style="background:#f8f9fa;">
                <td style="border:1px solid #dee2e6;"><strong>Revenue</strong></td>
                <td style="border:1px solid #dee2e6;">${summary_stats['total_revenue']:,.2f}</td>
              </tr>
              <tr>
                <td style="border:1px solid #dee2e6;"><strong>Orders</strong></td>
                <td style="border:1px solid #dee2e6;">{summary_stats['total_orders']}</td>
              </tr>
            </table>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family:Arial,sans-serif;color:#212529;line-height:1.6;max-width:600px;margin:auto;">
          <div style="background:#2E75B6;color:white;padding:20px;border-radius:4px 4px 0 0;">
            <h2 style="margin:0;">{business_name}</h2>
            <p style="margin:4px 0 0 0;opacity:0.9;">Daily Sales Briefing — {date_str}</p>
          </div>
          <div style="padding:20px;background:#ffffff;border:1px solid #dee2e6;border-top:none;border-radius:0 0 4px 4px;">
            <p>Good morning,</p>
            <p>Your Daily Sales Briefing is ready. The full report is attached as a PDF.</p>
            {stats_html}
            <hr style="border:none;border-top:1px solid #dee2e6;margin-top:24px;">
            <p style="font-size:12px;color:#6c757d;text-align:center;">
              Daily Sales Briefing — Community Edition<br>
              Generated at {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </p>
          </div>
        </body>
        </html>
        """


def send_briefing_email(config, analyzer, pdf_path, business_name):
    """
    Convenience function to send the briefing.
    Checks environment variables first, falls back to config values.
    """
    # Environment variables take priority (security best practice)
    sender_email = os.environ.get('BRIEFING_SMTP_EMAIL') or config['sender_email']
    sender_password = os.environ.get('BRIEFING_SMTP_PASSWORD') or config['sender_password']
    
    if not sender_email or 'your-email' in sender_email:
        raise ValueError(
            "Sender email not configured. Set BRIEFING_SMTP_EMAIL env var "
            "or update config.ini"
        )
    if not sender_password or 'your-app-password' in sender_password:
        raise ValueError(
            "Sender password not configured. Set BRIEFING_SMTP_PASSWORD env var "
            "or update config.ini"
        )
    
    sender = EmailSender(
        smtp_server=config['smtp_server'],
        smtp_port=int(config['smtp_port']),
        sender_email=sender_email,
        sender_password=sender_password,
        use_tls=config.get('use_tls', 'true').lower() == 'true'
    )
    
    summary = analyzer.daily_summary()
    alerts = analyzer.generate_alerts()
    
    sender.send_report(
        recipient_email=config['recipient_email'],
        business_name=business_name,
        pdf_path=pdf_path,
        summary_stats=summary,
        alerts=alerts
    )


if __name__ == '__main__':
    print("=" * 60)
    print("EMAIL SENDER — Test Mode")
    print("=" * 60)
    print()
    print("This module needs a real email configuration to run.")
    print("Configure your credentials in config/config.ini")
    print()
    print("For Gmail, you need to:")
    print("  1. Enable 2-Factor Authentication")
    print("  2. Generate an App Password at:")
    print("     https://myaccount.google.com/apppasswords")
    print("  3. Use that App Password in config.ini (NOT your main password)")
    print()
    print("Once configured, run: python3 main.py")
