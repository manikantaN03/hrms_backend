"""
Reset Superadmin Password
Resets password to default value from .env
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_db_context
from app.core.security import get_password_hash
from app.core.config import settings
from app.repositories.user_repository import UserRepository


def reset_password():
    """Reset superadmin password to default."""
    
    print("\n" + "=" * 70)
    print("RESET SUPERADMIN PASSWORD")
    print("=" * 70)
    
    try:
        with get_db_context() as db:
            user_repo = UserRepository(db)
            superadmin = user_repo.get_by_email(settings.SUPERADMIN_EMAIL)
            
            if not superadmin:
                print(f"\n✗ Superadmin not found: {settings.SUPERADMIN_EMAIL}")
                print(f"\nCreate superadmin first:")
                print(f"  python scripts/init_db.py")
                return False
            
            # Update password and verify email
            superadmin.hashed_password = get_password_hash(settings.SUPERADMIN_PASSWORD)
            superadmin.is_email_verified = True
            
            db.commit()
            db.refresh(superadmin)
            
            print(f"\n✓ Password reset successful!")
            print(f"\nLogin Credentials:")
            print(f"  Email: {settings.SUPERADMIN_EMAIL}")
            print(f"  Password: {settings.SUPERADMIN_PASSWORD}")
            print(f"\n⚠️  Change this password after first login!")
            print("\n" + "=" * 70)
            
            return True
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = reset_password()
    sys.exit(0 if success else 1)