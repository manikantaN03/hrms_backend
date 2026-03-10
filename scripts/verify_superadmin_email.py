"""
Mark superadmin email as verified
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_db_context
from app.core.config import settings
from app.repositories.user_repository import UserRepository
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_superadmin_email():
    """Mark superadmin email as verified"""
    print("\n" + "=" * 70)
    print("VERIFY SUPERADMIN EMAIL")
    print("=" * 70)
    
    try:
        with get_db_context() as db:
            user_repo = UserRepository(db)
            
            # Get superadmin
            superadmin = user_repo.get_by_email(settings.SUPERADMIN_EMAIL)
            
            if not superadmin:
                print(f"\n❌ Superadmin not found: {settings.SUPERADMIN_EMAIL}")
                return False
            
            # Update email verification
            superadmin.is_email_verified = True
            superadmin.email_otp = None
            superadmin.otp_created_at = None
            superadmin.otp_attempts = 0
            
            db.commit()
            db.refresh(superadmin)
            
            print(f"\n✅ Superadmin email verified!")
            print(f"  Email: {superadmin.email}")
            print(f"  Verified: {superadmin.is_email_verified}")
            print("\n" + "=" * 70)
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_superadmin_email()
    sys.exit(0 if success else 1)