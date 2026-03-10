"""
Delete and recreate superadmin account
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_db_context
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.user import User
from app.schemas.enums import UserRole, UserStatus
from app.repositories.user_repository import UserRepository
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_superadmin():
    """Delete existing superadmin and create new one"""
    print("\n" + "=" * 70)
    print("RECREATE SUPERADMIN ACCOUNT")
    print("=" * 70)
    
    confirm = input(f"\nThis will DELETE existing superadmin and create new one.\nContinue? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Operation cancelled")
        return False
    
    try:
        with get_db_context() as db:
            user_repo = UserRepository(db)
            
            # Delete existing superadmin
            existing = user_repo.get_by_email(settings.SUPERADMIN_EMAIL)
            if existing:
                db.delete(existing)
                db.commit()
                print(f"\n✓ Deleted existing superadmin (ID: {existing.id})")
            
            # Create new superadmin
            superadmin_data = {
                "name": settings.SUPERADMIN_NAME,
                "email": settings.SUPERADMIN_EMAIL,
                "hashed_password": get_password_hash(settings.SUPERADMIN_PASSWORD),
                "role": UserRole.SUPERADMIN,
                "status": UserStatus.ACTIVE,
                "is_email_verified": True,
                "phone_number": "+1234567890",
                "currency": "USD",
                "language": "English",
                "email_otp": None,
                "otp_created_at": None,
                "otp_attempts": 0
            }
            
            new_superadmin = user_repo.create(superadmin_data)
            
            print(f"\n✅ Superadmin created successfully!")
            print(f"\n📋 Details:")
            print(f"  ID: {new_superadmin.id}")
            print(f"  Name: {new_superadmin.name}")
            print(f"  Email: {new_superadmin.email}")
            print(f"  Role: {new_superadmin.role}")
            print(f"  Status: {new_superadmin.status}")
            print(f"  Email Verified: {new_superadmin.is_email_verified}")
            
            print(f"\n📋 Login Credentials:")
            print(f"  Email: {settings.SUPERADMIN_EMAIL}")
            print(f"  Password: {settings.SUPERADMIN_PASSWORD}")
            
            print(f"\n⚠️  IMPORTANT: Change password after first login!")
            print("\n" + "=" * 70)
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = recreate_superadmin()
    sys.exit(0 if success else 1)