import smtplib
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 60)
print("GMAIL ACCOUNT DIAGNOSTIC")
print("=" * 60)

email = os.getenv("SMTP_USERNAME", "")
password = os.getenv("SMTP_PASSWORD", "")

print(f"\nEmail: {email}")
print(f"Password length: {len(password)}")

# Test 1: Check account exists
print("\n[Test 1] Checking if account exists...")
try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    print("✅ Gmail server is reachable")
    server.quit()
except Exception as e:
    print(f"❌ Cannot reach Gmail: {e}")
    exit(1)

# Test 2: Check 2FA and App Password
print("\n[Test 2] Testing authentication...")
print("Please verify at: https://myaccount.google.com/security")
print("  - 2-Step Verification: Must be ON")
print("  - App Passwords available: Must see the option")

response = input("\nIs 2FA enabled? (yes/no): ").lower()
if response != 'yes':
    print("\n❌ You MUST enable 2FA first!")
    print("Go to: https://myaccount.google.com/security")
    exit(1)

response = input("Did you generate App Password TODAY? (yes/no): ").lower()
if response != 'yes':
    print("\n❌ Generate a NEW App Password!")
    print("Go to: https://myaccount.google.com/apppasswords")
    exit(1)

# Test 3: Actual login
print("\n[Test 3] Testing actual login...")
try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls(context=ssl.create_default_context())
    server.login(email, password)
    print("✅ LOGIN SUCCESSFUL!")
    server.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ Authentication failed: {e}")
    print("\nYour App Password is WRONG.")
    print("\nSTEPS TO FIX:")
    print("1. Go to: https://myaccount.google.com/apppasswords")
    print("2. Delete ALL existing passwords")
    print("3. Generate NEW password")
    print("4. Copy it WITHOUT spaces")
    print("5. Update .env file")
    print("6. Close terminal and open new one")
    print("7. Try again")
except Exception as e:
    print(f"❌ Unexpected error: {e}")