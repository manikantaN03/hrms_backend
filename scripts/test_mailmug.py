"""
Mailmug SMTP Configuration Auto-Detection
Tests different SMTP configurations and finds the working one
"""

import sys
from pathlib import Path
import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


async def test_smtp_config(host, port, username, password, use_tls=False, use_starttls=False):
    """Test a specific SMTP configuration."""
    config_desc = f"{host}:{port} (TLS={use_tls}, STARTTLS={use_starttls})"
    
    try:
        # Connect based on config
        if use_tls:
            smtp = aiosmtplib.SMTP(hostname=host, port=port, use_tls=True, timeout=30)
            await smtp.connect()
            print(f"  ✓ Connected with implicit TLS")
        else:
            smtp = aiosmtplib.SMTP(hostname=host, port=port, timeout=30)
            await smtp.connect()
            print(f"  ✓ Connected")
            
            if use_starttls:
                if smtp.supports_extension("STARTTLS"):
                    await smtp.starttls()
                    print(f"  ✓ STARTTLS successful")
                else:
                    print(f"  ✗ STARTTLS not supported")
                    return False, "STARTTLS not supported"
        
        # Login
        await smtp.login(username, password)
        print(f"  ✓ Authentication successful")
        
        # Disconnect
        await smtp.quit()
        print(f"  ✓ Disconnected")
        
        return True, "Success"
        
    except aiosmtplib.SMTPAuthenticationError as e:
        print(f"  ✗ Authentication failed: {e}")
        return False, f"Auth failed: {e}"
    except aiosmtplib.SMTPConnectError as e:
        print(f"  ✗ Connection failed: {e}")
        return False, f"Connection failed: {e}"
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False, f"Error: {e}"


async def auto_detect_config():
    """Auto-detect working SMTP configuration."""
    print("\n" + "=" * 70)
    print("MAILMUG SMTP AUTO-DETECTION")
    print("=" * 70)
    
    username = settings.SMTP_USERNAME
    password = settings.SMTP_PASSWORD
    host = settings.SMTP_HOST
    
    print(f"\nTesting with:")
    print(f"  Host: {host}")
    print(f"  Username: {username}")
    print(f"  Password: {'*' * len(password)}")
    
    # Test configurations
    configs = [
        (587, False, True, "Port 587 with STARTTLS (Recommended)"),
        (2525, False, False, "Port 2525 Plain (No encryption)"),
        (465, True, False, "Port 465 with SSL/TLS (Implicit)"),
        (25, False, False, "Port 25 Plain (Legacy)"),
    ]
    
    working_configs = []
    
    for port, use_tls, use_starttls, description in configs:
        print(f"\n{'─' * 70}")
        print(f"Testing: {description}")
        print(f"{'─' * 70}")
        
        success, message = await test_smtp_config(
            host, port, username, password, use_tls, use_starttls
        )
        
        if success:
            working_configs.append({
                'port': port,
                'use_tls': use_tls,
                'use_starttls': use_starttls,
                'description': description
            })
    
    # Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    if working_configs:
        print(f"\n✓ Found {len(working_configs)} working configuration(s):\n")
        
        for i, config in enumerate(working_configs, 1):
            print(f"{i}. {config['description']}")
            print(f"   SMTP_PORT={config['port']}")
            print(f"   SMTP_USE_TLS={config['use_tls']}")
            print(f"   SMTP_USE_STARTTLS={config['use_starttls']}")
            print()
        
        # Recommend best config
        best = working_configs[0]
        print("RECOMMENDED .env CONFIGURATION:")
        print("-" * 70)
        print(f"SMTP_HOST={host}")
        print(f"SMTP_PORT={best['port']}")
        print(f"SMTP_USE_TLS={best['use_tls']}")
        print(f"SMTP_USE_STARTTLS={best['use_starttls']}")
        print(f"SMTP_USERNAME={username}")
        print(f"SMTP_PASSWORD={password}")
        print("-" * 70)
        
        return best
    else:
        print("\n✗ No working configuration found!")
        print("\nPossible issues:")
        print("  - Wrong credentials")
        print("  - Account not activated")
        print("  - IP blocked")
        print("  - Firewall issues")
        
        return None


async def main():
    """Run auto-detection."""
    config = await auto_detect_config()
    
    if config:
        print("\n" + "=" * 70)
        print("✓ AUTO-DETECTION COMPLETE!")
        print("=" * 70)
    
    return config is not None


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)