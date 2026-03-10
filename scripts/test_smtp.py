# server/scripts/test_smtp_detailed.py

import sys
from pathlib import Path
import asyncio
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def test_smtp():
    print("\n" + "=" * 70)
    print("SMTP CONFIGURATION TEST")
    print("=" * 70)
    print(f"Host: {settings.SMTP_HOST}")
    print(f"Port: {settings.SMTP_PORT}")
    print(f"Username: {settings.SMTP_USERNAME}")
    print(f"From: {settings.SMTP_FROM_EMAIL}")
    print(f"Use TLS: {settings.SMTP_USE_TLS}")
    print(f"Use STARTTLS: {settings.SMTP_USE_STARTTLS}")
    print("=" * 70)
    
    try:
        # Create test message
        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = "reddykowsik3@gmail.com"  # Your email
        message["Subject"] = "🧪 SMTP Test - Levitica HR"
        
        text = "This is a test email. If you receive this, SMTP is working!"
        html = """
        <html>
          <body>
            <h2>✅ SMTP Test Successful!</h2>
            <p>This is a test email from <strong>Levitica HR System</strong>.</p>
            <p>If you're seeing this, your SMTP configuration is working correctly.</p>
            <hr>
            <p style="font-size: 12px; color: #666;">
              Sent via: {}<br>
              Port: {}<br>
              Time: Now
            </p>
          </body>
        </html>
        """.format(settings.SMTP_HOST, settings.SMTP_PORT)
        
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        print("\n📤 Sending test email...")
        
        response = await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_USE_STARTTLS,
            use_tls=settings.SMTP_USE_TLS,
            timeout=30,
        )
        
        print(f"✅ Email sent successfully!")
        print(f"Response: {response}")
        print("\n📬 Check your inbox (and spam folder): reddykowsik3@gmail.com")
        print("=" * 70)
        return True
        
    except aiosmtplib.SMTPException as e:
        print(f"\n❌ SMTP Error: {e}")
        print("\nPossible issues:")
        print("  1. Invalid credentials")
        print("  2. SMTP server unreachable")
        print("  3. Port blocked by firewall")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_smtp())