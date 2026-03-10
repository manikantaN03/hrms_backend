"""
Validate HRMS setup - check if all required components are properly configured
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.models.business import Business
from app.models.user import User
from app.models.employee import Employee
from app.core.database import get_db_context
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def validate_setup():
    """Validate that the HRMS setup is complete and working"""
    logger.info("🔍 Validating HRMS setup...")
    
    try:
        with get_db_context() as db:
            # Check superadmin
            superadmin = db.query(User).filter(User.email == settings.SUPERADMIN_EMAIL).first()
            if not superadmin:
                logger.error("❌ Superadmin not found")
                return False
            logger.info(f"✅ Superadmin found: {superadmin.email}")
            
            # Check business
            business = db.query(Business).first()
            if not business:
                logger.error("❌ No business found")
                return False
            logger.info(f"✅ Business found: {business.business_name}")
            
            # Check employees
            employee_count = db.query(Employee).count()
            logger.info(f"✅ Employees in database: {employee_count}")
            
            # Check database connection
            logger.info(f"✅ Database connection: {settings.DB_NAME}@{settings.DB_HOST}:{settings.DB_PORT}")
            
            logger.info("\n🎉 Setup validation completed successfully!")
            logger.info("\nNext steps:")
            logger.info("1. Start the application: uvicorn app.main:app --reload")
            logger.info("2. Open API docs: http://localhost:8000/docs")
            logger.info(f"3. Login with: {settings.SUPERADMIN_EMAIL} / Admin@123")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_setup()
    sys.exit(0 if success else 1)