"""
Superadmin Account Verification
Checks if superadmin exists and credentials are correct
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_db_context
from app.core.config import settings
from app.core.security import verify_password
from app.repositories.user_repository import UserRepository


def check_superadmin():
    """Verify superadmin account status."""
    
    print("\n" + "=" * 70)
    print("SUPERADMIN ACCOUNT VERIFICATION")
    print("=" * 70)
    
    print(f"\nExpected Credentials:")
    print(f"  Email: {settings.SUPERADMIN_EMAIL}")
    print(f"  Password: {settings.SUPERADMIN_PASSWORD}")
    
    try:
        with get_db_context() as db:
            user_repo = UserRepository(db)
            superadmin = user_repo.get_by_email(settings.SUPERADMIN_EMAIL)
            
            if not superadmin:
                print(f"\n✗ Superadmin NOT FOUND!")
                print(f"\nTo create superadmin:")
                print(f"  python scripts/init_db.py")
                return False
            
            # Display account info
            print(f"\n✓ Superadmin found:")
            print(f"  ID: {superadmin.id}")
            print(f"  Name: {superadmin.name}")
            print(f"  Email: {superadmin.email}")
            print(f"  Role: {superadmin.role.value}")
            print(f"  Status: {superadmin.status.value}")
            print(f"  Has Password: {'✓' if superadmin.hashed_password else '✗'}")
            print(f"  Email Verified: {'✓' if superadmin.is_email_verified else '✗'}")
            
            # Test password
            if superadmin.hashed_password:
                print(f"\nTesting password...")
                
                is_valid = verify_password(
                    settings.SUPERADMIN_PASSWORD,
                    superadmin.hashed_password
                )
                
                if is_valid:
                    print(f"  ✓ Password is correct")
                else:
                    print(f"  ✗ Password is incorrect!")
                    print(f"\nTo reset password:")
                    print(f"  python scripts/reset_superadmin_password.py")
                    return False
            else:
                print(f"\n✗ No password set!")
                print(f"To reset:")
                print(f"  python scripts/reset_superadmin_password.py")
                return False
            
            # Check email verification
            if not superadmin.is_email_verified:
                print(f"\n⚠️  Email not verified!")
                print(f"To fix:")
                print(f"  python scripts/verify_superadmin_email.py")
                return False
            
            print("\n" + "=" * 70)
            print("✓ SUPERADMIN ACCOUNT OK")
            print("=" * 70)
            
            return True
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_superadmin()
    sys.exit(0 if success else 1)