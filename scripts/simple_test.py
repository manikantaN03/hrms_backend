# scripts/simple_test.py
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.mailmug.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))  # Changed to 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

print("="*50)
print("VERIFYING CREDENTIALS FOR TEST")
print(f"Host: {SMTP_HOST}")
print(f"Port: {SMTP_PORT}")
print(f"Username: {SMTP_USERNAME}")
if SMTP_PASSWORD and len(SMTP_PASSWORD) == 16:
    print(f"Password: {'*' * 12}{SMTP_PASSWORD[-4:]} (16 characters found)")
else:
    print(f"Password: Length: {len(SMTP_PASSWORD) if SMTP_PASSWORD else 0}")
print("="*50)

try:
    print("\n[1] Connecting to server...")
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
    print("    ✅ Connected to SMTP server.")
    
    # Check what the server supports
    print("\n[2] Checking server capabilities...")
    server.ehlo()
    if server.has_extn('STARTTLS'):
        print("    ✅ Server supports STARTTLS")
        print("[3] Starting TLS...")
        server.starttls()
        server.ehlo()  # Re-identify after STARTTLS
        print("    ✅ TLS started.")
    else:
        print("    ⚠️  Server does NOT support STARTTLS")
        print("    Continuing without encryption...")

    print("\n[4] Attempting to log in...")
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    print("    ✅ Login successful!")

    print("\n[5] Sending test email...")
    sender_email = SMTP_USERNAME
    receiver_email = "reddykowsik3@gmail.com"
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "✅ Test from Mailmug SMTP"
    message["From"] = sender_email
    message["To"] = receiver_email
    
    text = "This is a test email from Mailmug SMTP. It worked!"
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #4CAF50;">✅ SMTP Test Successful!</h2>
        <p>Your Mailmug SMTP configuration is working correctly.</p>
        
        <h3>Configuration:</h3>
        <ul>
          <li><strong>Host:</strong> {SMTP_HOST}</li>
          <li><strong>Port:</strong> {SMTP_PORT}</li>
          <li><strong>From:</strong> {sender_email}</li>
        </ul>
        
        <hr>
        <p style="font-size: 12px; color: #666;">
          This is an automated test email from Levitica HR System
        </p>
      </body>
    </html>
    """
    
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))
    
    server.sendmail(sender_email, receiver_email, message.as_string())
    print("    ✅ Email sent successfully!")
    
    server.quit()
    
    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED!")
    print("="*50)
    print(f"📬 Check inbox: {receiver_email}")
    print("   (Also check spam/junk folder)")
    print("="*50)

except smtplib.SMTPAuthenticationError as e:
    print("\n❌ AUTHENTICATION FAILED.")
    print(f"   Server response: {e}")
    print("\n   Check your Mailmug credentials at:")
    print("   https://mailmug.net/dashboard")

except smtplib.SMTPException as e:
    print(f"\n❌ SMTP Error: {e}")

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest finished.")