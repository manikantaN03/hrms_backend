"""
Script to drop PostgreSQL database
⚠️ WARNING: This will delete all data!
"""
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_database():
    """Drop PostgreSQL database"""
    logger.warning("=" * 60)
    logger.warning("⚠️  WARNING: Dropping Database!")
    logger.warning("=" * 60)
    
    # Confirmation
    confirm = input(f"Are you sure you want to drop '{settings.DB_NAME}'? (yes/no): ")
    if confirm.lower() != 'yes':
        logger.info("Operation cancelled")
        return False
    
    try:
        # Connect to PostgreSQL server
        connection = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database='postgres'
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        
        # Terminate existing connections
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{settings.DB_NAME}'
            AND pid <> pg_backend_pid()
        """)
        
        # Drop database
        cursor.execute(f'DROP DATABASE IF EXISTS {settings.DB_NAME}')
        logger.info(f"✓ Database '{settings.DB_NAME}' dropped successfully!")
        
        cursor.close()
        connection.close()
        
        logger.info("=" * 60)
        return True
    
    except Exception as e:
        logger.error(f"✗ Error dropping database: {str(e)}")
        return False

if __name__ == "__main__":
    success = drop_database()
    sys.exit(0 if success else 1)