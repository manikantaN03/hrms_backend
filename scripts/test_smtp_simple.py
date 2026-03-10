import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "mail.leviticatechnologies.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
USE_TLS = os.getenv("SMTP_USE_TLS", "True") == "True"

print("="*70)
print("SMTP CONNECTION TEST")
print("="*70)
print(f"Host: {SMTP_HOST}")
print(f"Port: {SMTP_PORT}")
print(f"Username: {SMTP_USERNAME}")
print(f"SSL/TLS: {USE_TLS}")
print("="*70)

try:
    if USE_TLS:
        print("\n[1] Connecting with SSL/TLS (port 465)...")
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=30)
    else:
        print("\n[1] Connecting with STARTTLS (port 587)...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        server.starttls(context=ssl.create_default_context())
    
    print("✅ Connected to SMTP server")
    
    print("\n[2] Attempting login...")
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    print("✅ Login successful")
    
    print("\n[3] Sending test email...")
    message = MIMEMultipart("alternative")
    message["From"] = SMTP_USERNAME
    message["To"] = "oldyear2120@gmail.com"
    message["Subject"] = "Test Email - Levitica HR"
    
    html = """
    <html>
      <body>
        <h2>✅ Test Email Successful!</h2>
        <p>Your SMTP configuration is working.</p>
      </body>
    </html>
    """
    
    message.attach(MIMEText(html, "html"))
    
    server.sendmail(SMTP_USERNAME, "oldyear2120@gmail.com", message.as_string())
    print("✅ Email sent successfully!")
    
    server.quit()
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)
    print("\n📬 Check inbox: oldyear2120@gmail.com")
    print("(Also check spam/junk folder)")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ Authentication failed: {e}")
    print("\nPossible issues:")
    print("  - Wrong username or password")
    print("  - Account locked or disabled")
    
except smtplib.SMTPConnectError as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nPossible issues:")
    print("  - SMTP server is down")
    print("  - Port is blocked by firewall")
    print("  - Wrong host/port combination")
    
except TimeoutError as e:
    print(f"\n❌ Connection timeout: {e}")
    print("\nPossible issues:")
    print("  - SMTP server is slow/unreachable")
    print("  - Firewall blocking the port")
    print("  - Wrong port number")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()