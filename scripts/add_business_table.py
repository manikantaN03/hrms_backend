"""
Add Business Table to Database
Run this after creating the Business model
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.models.base import Base
from app.models.business import Business
from app.core.database import engine
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_business_table():
    """Create business table"""
    
    print("\n" + "=" * 70)
    print("ADDING BUSINESS TABLE")
    print("=" * 70)
    print(f"Database: {settings.DB_NAME}")
    print(f"Host: {settings.DB_HOST}:{settings.DB_PORT}")
    print("=" * 70)
    
    try:
        # Create table
        logger.info("\nCreating 'businesses' table...")
        Base.metadata.tables['businesses'].create(bind=engine, checkfirst=True)
        
        # Verify
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'businesses'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
        
        if columns:
            logger.info(f"\n✓ Table created with {len(columns)} columns:")
            for col_name, col_type in columns:
                print(f"  - {col_name}: {col_type}")
        
        print("\n" + "=" * 70)
        print("✓ Business table created successfully!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_business_table()
    sys.exit(0 if success else 1)