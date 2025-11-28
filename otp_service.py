import random
import string
from datetime import datetime, timedelta
import os
import httpx


class OTPService:
    """
    Service for OTP generation and verification
    """

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """
        Generate a random OTP code

        Args:
            length: Length of OTP code (default: 6)

        Returns:
            OTP code as string
        """
        # Generate numeric OTP
        otp = ''.join(random.choices(string.digits, k=length))
        return otp

    @staticmethod
    def is_otp_valid(otp_created_at: datetime, expiry_minutes: int = 5) -> bool:
        """
        Check if OTP is still valid (not expired)

        Args:
            otp_created_at: When the OTP was created
            expiry_minutes: OTP expiry time in minutes (default: 5)

        Returns:
            True if OTP is still valid, False otherwise
        """
        if not otp_created_at:
            return False

        now = datetime.utcnow()
        expiry_time = otp_created_at + timedelta(minutes=expiry_minutes)
        return now <= expiry_time

    @staticmethod
    async def send_otp(phone: str, otp: str) -> bool:
        """
        Send OTP to user's phone number using Faraz SMS Pattern (Iran Payamak).

        Pattern: کد ورود شما: %code1% code : %code% شرکت صفر و یک

        NOTE: Currently in testing mode - OTP is returned in API response instead of SMS.
        SMS sending is disabled until the correct API endpoint is configured.

        Args:
            phone: User's phone number
            otp: OTP code to send

        Returns:
            True if sent successfully, False otherwise
        """
        # TESTING MODE: Skip actual SMS sending, just log to console
        print(f"\n{'='*50}")
        print(f"📱 OTP REQUEST - Testing Mode")
        print(f"📱 Phone: {phone}")
        print(f"🔐 OTP Code: {otp}")
        print(f"📄 Pattern: کد ورود شما: {otp} code : {otp} شرکت صفر و یک")
        print(f"⏰ Valid for 5 minutes")
        print(f"ℹ️  OTP is included in API response for testing")
        print(f"{'='*50}\n")

        # Return success without sending actual SMS
        return True

        # TODO: Re-enable SMS sending when correct API endpoint is available
        # Get Faraz SMS credentials from environment
        # faraz_username = os.getenv("FARAZ_SMS_USERNAME")
        # faraz_password = os.getenv("FARAZ_SMS_PASSWORD")
        # faraz_from_number = os.getenv("FARAZ_SMS_FROM_NUMBER")
        # faraz_pattern_code = os.getenv("FARAZ_SMS_PATTERN_CODE")
        #
        # try:
        #     # Faraz SMS Pattern API endpoint
        #     url = "https://rest.payamak-panel.com/api/SendSMS/SendByBaseNumber"
        #
        #     # Prepare request payload for pattern-based SMS
        #     payload = {
        #         "username": faraz_username,
        #         "password": faraz_password,
        #         "to": phone,
        #         "bodyId": int(faraz_pattern_code) if faraz_pattern_code else 0,
        #         "text": f"{otp};{otp}"  # Parameters: code1;code (separated by semicolon)
        #     }
        #
        #     # Send HTTP POST request
        #     async with httpx.AsyncClient() as client:
        #         response = await client.post(
        #             url,
        #             json=payload,
        #             headers={"Content-Type": "application/json"},
        #             timeout=10.0
        #         )
        #
        #         # Check response
        #         if response.status_code == 200:
        #             result = response.json()
        #             # Faraz SMS returns various status codes
        #             # Check for successful sending
        #             if result.get("Value") or result.get("RetStatus") == 1:
        #                 print(f"✅ OTP sent successfully to {phone} using pattern")
        #                 return True
        #             else:
        #                 print(f"❌ Faraz SMS API error: {result}")
        #                 return False
        #         else:
        #             print(f"❌ HTTP Error {response.status_code}: {response.text}")
        #             return False
        #
        # except Exception as e:
        #     print(f"❌ Failed to send OTP via Faraz SMS: {str(e)}")
        #     return False
