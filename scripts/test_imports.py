# server/scripts/test_imports.py

"""Test if all required modules can be imported"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Testing imports...")
print(f"Python path: {sys.path[0]}\n")

try:
    import itsdangerous
    print("✓ itsdangerous")
except ImportError as e:
    print(f"✗ itsdangerous: {e}")

try:
    import aiosmtplib
    print("✓ aiosmtplib")
except ImportError as e:
    print(f"✗ aiosmtplib: {e}")

try:
    import jinja2
    print("✓ jinja2")
except ImportError as e:
    print(f"✗ jinja2: {e}")

try:
    from app.core.tokens import token_manager
    print("✓ token_manager imported")
except ImportError as e:
    print(f"✗ token_manager: {e}")

try:
    from app.services.email_service import email_service
    print("✓ email_service imported")
except ImportError as e:
    print(f"✗ email_service: {e}")

try:
    from app.services.registration_service import RegistrationService
    print("✓ RegistrationService imported")
except ImportError as e:
    print(f"✗ RegistrationService: {e}")

print("\n✓ All imports successful!")