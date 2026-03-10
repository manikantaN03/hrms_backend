"""
Database Initialization
Creates tables and superadmin account
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.models.base import Base
from app.models.user import User
from app.schemas.enums import UserRole, UserStatus
from app.core.database import engine, get_db_context, check_db_connection
from app.core.security import get_password_hash
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def verify_connection():
    """Verify database is accessible."""
    logger.info("Checking database connection...")
    
    if not check_db_connection():
        logger.error("Cannot connect to database!")
        logger.error("")
        logger.error("Please ensure:")
        logger.error(f"  1. PostgreSQL is running")
        logger.error(f"  2. Database '{settings.DB_NAME}' exists")
        logger.error(f"  3. Credentials in .env are correct")
        logger.error("")
        logger.error("To create database:")
        logger.error("  python scripts/create_db.py")
        return False
    
    logger.info("Database connection verified")
    return True


def create_tables():
    """Create all database tables."""
    logger.info("\nCreating tables...")
    
    try:
        Base.metadata.create_all(bind=engine)
        
        # Verify tables created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
        
        if tables:
            logger.info(f"Tables created: {', '.join(tables)}")
            return True
        else:
            logger.warning("No tables found after creation")
            return False
            
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
        return False


def create_superadmin():
    """Create superadmin account."""
    logger.info("\nCreating superadmin...")
    
    try:
        with get_db_context() as db:
            # Check if exists
            existing = db.query(User).filter(
                User.email == settings.SUPERADMIN_EMAIL
            ).first()
            
            if existing:
                logger.info(f"Superadmin already exists: {settings.SUPERADMIN_EMAIL}")
                return existing
            
            # Create new superadmin
            superadmin = User(
                name=settings.SUPERADMIN_NAME,
                email=settings.SUPERADMIN_EMAIL,
                hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
                role=UserRole.SUPERADMIN,
                status=UserStatus.ACTIVE,
                is_email_verified=True,
                phone_number="+1234567890",
                currency="USD",
                language="English"
            )
            
            db.add(superadmin)
            db.commit()
            db.refresh(superadmin)
            
            logger.info(f"Superadmin created successfully!")
            logger.info(f"  ID: {superadmin.id}")
            logger.info(f"  Email: {settings.SUPERADMIN_EMAIL}")
            logger.info(f"  Password: {settings.SUPERADMIN_PASSWORD}")
            logger.warning("  ⚠️  Change the default password immediately!")
            
            return superadmin
            
    except IntegrityError as e:
        logger.error(f"Superadmin creation failed (duplicate?): {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def main():
    """Run database initialization."""
    print("\n" + "=" * 70)
    print("LEVITICA HR - Database Initialization")
    print("=" * 70)
    print(f"Database: {settings.DB_NAME}")
    print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print("=" * 70)
    
    # Step 1: Verify connection
    if not verify_connection():
        return False
    
    # Step 2: Create tables
    if not create_tables():
        return False
    
    # Step 3: Create superadmin
    try:
        create_superadmin()
    except Exception:
        return False
    
    # Success
    print("\n" + "=" * 70)
    print("✓ Initialization complete!")
    print("=" * 70)
    print("\nStart the application:")
    print("  uvicorn app.main:app --reload")
    print("\nAccess documentation:")
    print("  http://localhost:8000/docs")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nFatal error: {e}")
        sys.exit(1)