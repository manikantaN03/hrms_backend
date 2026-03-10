"""
Script to create PostgreSQL database
Run this before init_db.py if database doesn't exist
"""
import sys
from pathlib import Path
from urllib.parse import quote_plus

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("=" * 60)
    print("ERROR: psycopg2 not installed!")
    print("=" * 60)
    print("Install it with: pip install psycopg2-binary")
    print("=" * 60)
    sys.exit(1)

from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test basic PostgreSQL connection"""
    try:
        logger.info(f"Testing connection to PostgreSQL...")
        logger.info(f"Host: {settings.DB_HOST}")
        logger.info(f"Port: {settings.DB_PORT}")
        logger.info(f"User: {settings.DB_USER}")
        
        connection = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database='postgres',
            connect_timeout=5
        )
        connection.close()
        logger.info("✓ Connection successful")
        return True
    except psycopg2.OperationalError as e:
        logger.error(f"✗ Connection failed: {str(e)}")
        return False

def create_database():
    """Create PostgreSQL database if it doesn't exist"""
    logger.info("=" * 60)
    logger.info("Creating PostgreSQL Database...")
    logger.info("=" * 60)
    
    # First test connection
    if not test_connection():
        logger.error("")
        logger.error("Please ensure:")
        logger.error("  1. PostgreSQL is installed and running")
        logger.error("  2. Database credentials in .env are correct")
        logger.error("  3. PostgreSQL service is started")
        logger.error("")
        logger.error("To check PostgreSQL service on Windows:")
        logger.error("  - Press Win+R, type 'services.msc', press Enter")
        logger.error("  - Look for 'postgresql-x64-15' (or similar)")
        logger.error("  - Right-click and select 'Start' if not running")
        logger.error("")
        logger.error("Or use Docker:")
        logger.error("  docker-compose -f docker-compose-postgres.yml up -d")
        return False
    
    try:
        # Connect to PostgreSQL server (default 'postgres' database)
        logger.info(f"Connecting to PostgreSQL at {settings.DB_HOST}:{settings.DB_PORT}")
        connection = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database='postgres'
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (settings.DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if exists:
            logger.info(f"✓ Database '{settings.DB_NAME}' already exists")
        else:
            # Create database
            cursor.execute(f'CREATE DATABASE {settings.DB_NAME}')
            logger.info(f"✓ Database '{settings.DB_NAME}' created successfully!")
        
        cursor.close()
        connection.close()
        
        logger.info("=" * 60)
        logger.info("✓ Database setup complete!")
        logger.info(f"  Database: {settings.DB_NAME}")
        logger.info(f"  Host: {settings.DB_HOST}:{settings.DB_PORT}")
        logger.info(f"  User: {settings.DB_USER}")
        logger.info("=" * 60)
        return True
    
    except psycopg2.OperationalError as e:
        logger.error(f"✗ Cannot connect to PostgreSQL: {str(e)}")
        logger.error("")
        logger.error("Common issues:")
        logger.error("  1. PostgreSQL service not running")
        logger.error("  2. Wrong password in .env file")
        logger.error("  3. PostgreSQL not listening on specified port")
        logger.error("  4. Firewall blocking connection")
        return False
    except psycopg2.Error as e:
        logger.error(f"✗ PostgreSQL Error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_database()
    sys.exit(0 if success else 1)