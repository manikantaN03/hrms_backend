"""
Test SMS OTP functionality - Automated version
"""
import sys
from pathlib import Path
import asyncio

sys.path.append(str(Path(__file__).parent.parent))

from app.services.sms_service import sms_service
from app.core.config import settings

async def test_sms():
    print("\n" + "=" * 70)
    print("SMS CONFIGURATION TEST")
    print("=" * 70)
    print(f"Provider: {settings.SMS_PROVIDER}")
    
    if settings.SMS_PROVIDER == "twilio":
        print(f"Twilio Account SID: {settings.TWILIO_ACCOUNT_SID}")
        print(f"Twilio Phone: {settings.TWILIO_PHONE_NUMBER}")
    elif settings.SMS_PROVIDER == "msg91":
        print(f"MSG91 Auth Key: {settings.MSG91_AUTH_KEY}")
    elif settings.SMS_PROVIDER == "fast2sms":
        print(f"Fast2SMS API Key: {settings.FAST2SMS_API_KEY}")
    
    print("=" * 70)
    
    # Use the Twilio phone number from config as test number
    test_phone = "+919130000000"  # Replace with your actual phone number
    test_otp = "123456"
    
    print(f"\n📱 Sending test OTP '{test_otp}' to {test_phone}...")
    
    success = await sms_service.send_otp(test_phone, test_otp)
    
    if success:
        print(f"✅ SMS sent successfully!")
        print(f"📬 Check your phone: {test_phone}")
    else:
        print(f"❌ Failed to send SMS")
        print("\nPossible issues:")
        print("  1. Invalid credentials")
        print("  2. Insufficient balance")
        print("  3. Invalid phone number format")
        print("  4. SMS provider API error")
        print("  5. Phone number not verified (Twilio trial accounts)")
    
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_sms())
