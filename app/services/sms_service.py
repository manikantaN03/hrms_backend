"""
SMS Service for sending OTP via phone
Supports multiple SMS providers: Twilio, MSG91, Fast2SMS
"""
import logging
from typing import Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS messages"""
    
    def __init__(self):
        self.provider = settings.SMS_PROVIDER  # 'twilio', 'msg91', 'fast2sms'
        
    async def send_otp(self, phone_number: str, otp: str) -> bool:
        """
        Send OTP to phone number
        
        Args:
            phone_number: Phone number with country code (e.g., +919876543210)
            otp: 6-digit OTP code
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if self.provider == "twilio":
                return await self._send_via_twilio(phone_number, otp)
            elif self.provider == "msg91":
                return await self._send_via_msg91(phone_number, otp)
            elif self.provider == "fast2sms":
                return await self._send_via_fast2sms(phone_number, otp)
            else:
                logger.error(f"Unknown SMS provider: {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send SMS OTP: {e}")
            return False
    
    async def _send_via_twilio(self, phone_number: str, otp: str) -> bool:
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            
            message = client.messages.create(
                body=f"Your Levitica HR verification code is: {otp}. Valid for 10 minutes.",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            logger.info(f"SMS sent via Twilio: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Twilio SMS error: {e}")
            return False
    
    async def _send_via_msg91(self, phone_number: str, otp: str) -> bool:
        """Send SMS via MSG91"""
        try:
            url = "https://api.msg91.com/api/v5/otp"
            
            # Remove + from phone number for MSG91
            phone = phone_number.replace("+", "")
            
            payload = {
                "template_id": settings.MSG91_TEMPLATE_ID,
                "mobile": phone,
                "authkey": settings.MSG91_AUTH_KEY,
                "otp": otp
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"SMS sent via MSG91 to {phone_number}")
                    return True
                else:
                    logger.error(f"MSG91 error: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"MSG91 SMS error: {e}")
            return False
    
    async def _send_via_fast2sms(self, phone_number: str, otp: str) -> bool:
        """Send SMS via Fast2SMS"""
        try:
            url = "https://www.fast2sms.com/dev/bulkV2"
            
            # Remove +91 from phone number
            phone = phone_number.replace("+91", "").replace("+", "")
            
            headers = {
                "authorization": settings.FAST2SMS_API_KEY
            }
            
            payload = {
                "route": "otp",
                "variables_values": otp,
                "flash": 0,
                "numbers": phone
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    headers=headers, 
                    data=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info(f"SMS sent via Fast2SMS to {phone_number}")
                    return True
                else:
                    logger.error(f"Fast2SMS error: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Fast2SMS error: {e}")
            return False


# Singleton instance
sms_service = SMSService()
