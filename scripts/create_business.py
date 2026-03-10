"""
Create default business for the HRMS system
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.models.business import Business
from app.models.user import User
from app.core.database import get_db_context
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_default_business():
    """Create default business if it doesn't exist"""
    try:
        with get_db_context() as db:
            # Check if business already exists
            business = db.query(Business).first()
            if business:
                logger.info(f"Business already exists: {business.business_name}")
                return True
            
            # Get superadmin user
            superadmin = db.query(User).filter(User.email == settings.SUPERADMIN_EMAIL).first()
            if not superadmin:
                logger.error("Superadmin not found. Please run setup.py first to create superadmin.")
                return False
            
            # Create default business
            business = Business(
                owner_id=superadmin.id,
                business_name="Levitica Technologies Private Limited",
                gstin="22AAAAA0000A1Z5",
                is_authorized=True,
                pan="ABCDE1234F",
                address="123 Business Street, Tech City, Karnataka",
                city="Bangalore",
                pincode="560001",
                state="Karnataka",
                constitution="Private Limited Company",
                product="HRMS Suite",
                plan="Professional",
                employee_count=50,
                billing_frequency="Monthly (1 month)",
                business_url="levitica-tech",
                is_active=True
            )
            
            db.add(business)
            db.commit()
            db.refresh(business)
            
            logger.info(f"✓ Created default business: {business.business_name}")
            logger.info(f"  - Business ID: {business.id}")
            logger.info(f"  - Owner: {superadmin.email}")
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to create business: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_default_business()
    sys.exit(0 if success else 1)