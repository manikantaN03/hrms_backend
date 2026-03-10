"""
Test Redis Cloud Connection
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
import redis
import ssl


def test_redis_cloud():
    """Test Redis Cloud connection with optional SSL"""
    print("\n" + "=" * 70)
    print("REDIS CLOUD CONNECTION TEST")
    print("=" * 70)
    print(f"Host: {settings.REDIS_HOST}")
    print(f"Port: {settings.REDIS_PORT}")
    print(f"Username: {settings.REDIS_USERNAME}")
    print(f"Database: {settings.REDIS_DB}")
    print(f"SSL: {settings.REDIS_SSL}")
    print("=" * 70)
    
    try:
        # Test 1: Basic connection
        print("\n[Test 1] Connecting to Redis Cloud...")
        
        # Connection parameters
        conn_params = {
            'host': settings.REDIS_HOST,
            'port': settings.REDIS_PORT,
            'db': settings.REDIS_DB,
            'username': settings.REDIS_USERNAME,
            'password': settings.REDIS_PASSWORD,
            'decode_responses': settings.REDIS_DECODE_RESPONSES,
            'socket_connect_timeout': 10,
            'socket_timeout': 10
        }
        
        # Add SSL only if enabled
        if settings.REDIS_SSL:
            conn_params['ssl'] = True
            conn_params['ssl_cert_reqs'] = ssl.CERT_NONE
            conn_params['ssl_check_hostname'] = False
            print("  Using SSL connection...")
        else:
            print("  Using plain connection (no SSL)...")
        
        # Create Redis client
        r = redis.Redis(**conn_params)
        
        # Test ping
        ping_response = r.ping()
        print(f"  ✓ Ping response: {ping_response}")
        
        # Test 2: Set/Get operation
        print("\n[Test 2] Testing SET/GET operations...")
        
        # Set value
        success = r.set('test_key', 'Hello from Levitica HR!')
        print(f"  ✓ SET operation: {success}")
        
        # Get value
        result = r.get('test_key')
        print(f"  ✓ GET operation: {result}")
        
        # Test 3: Expiration
        print("\n[Test 3] Testing key expiration...")
        
        r.setex('temp_key', 5, 'Expires in 5 seconds')
        ttl = r.ttl('temp_key')
        print(f"  ✓ Key TTL: {ttl} seconds")
        
        # Test 4: Hash operations (for session storage)
        print("\n[Test 4] Testing HASH operations...")
        
        r.hset('user:1', mapping={
            'name': 'Test User',
            'email': 'test@example.com',
            'role': 'admin'
        })
        
        user_data = r.hgetall('user:1')
        print(f"  ✓ User data: {user_data}")
        
        # Test 5: Set operations (for tracking active sessions)
        print("\n[Test 5] Testing SET operations...")
        
        r.sadd('active_sessions:1', 'token1', 'token2', 'token3')
        sessions = r.smembers('active_sessions:1')
        print(f"  ✓ Active sessions: {sessions}")
        
        # Test 6: Server info
        print("\n[Test 6] Redis Cloud server info...")
        
        info = r.info()
        print(f"  Redis Version: {info.get('redis_version')}")
        print(f"  Connected Clients: {info.get('connected_clients')}")
        print(f"  Used Memory: {info.get('used_memory_human')}")
        print(f"  Total Commands: {info.get('total_commands_processed')}")
        print(f"  Uptime (days): {info.get('uptime_in_days')}")
        
        # Test 7: Session simulation
        print("\n[Test 7] Simulating session storage...")
        
        import json
        session_data = {
            'user_id': 1,
            'email': 'admin@example.com',
            'role': 'admin',
            'token': 'abc123xyz'
        }
        
        # Store session
        r.setex('session:abc123xyz', 1440, json.dumps(session_data))
        
        # Retrieve session
        stored_session = r.get('session:abc123xyz')
        if stored_session:
            retrieved = json.loads(stored_session)
            print(f"  ✓ Session stored and retrieved: {retrieved}")
        
        # Cleanup
        print("\n[Cleanup] Removing test keys...")
        r.delete('test_key', 'temp_key', 'user:1', 'active_sessions:1', 'session:abc123xyz')
        print("  ✓ Test keys deleted")
        
        # Success
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\n🎉 Redis Cloud is working correctly!")
        print("✓ Session management is ready to use")
        print("\nConnection Details:")
        print(f"  Host: {settings.REDIS_HOST}")
        print(f"  Port: {settings.REDIS_PORT}")
        print(f"  SSL: {'Enabled' if settings.REDIS_SSL else 'Disabled'}")
        print(f"  Database: {settings.REDIS_DB}")
        print("=" * 70)
        
        return True
        
    except redis.AuthenticationError as e:
        print(f"\n✗ Authentication failed: {e}")
        print("\n❌ Check your credentials:")
        print(f"  Username: {settings.REDIS_USERNAME}")
        print(f"  Password: {settings.REDIS_PASSWORD[:4]}...{settings.REDIS_PASSWORD[-4:]}")
        print("\n💡 Verify credentials in Redis Cloud dashboard:")
        print("  https://app.redislabs.com/")
        return False
        
    except redis.ConnectionError as e:
        error_msg = str(e)
        print(f"\n✗ Connection failed: {e}")
        print("\n❌ Troubleshooting:")
        
        if "SSL" in error_msg or "WRONG_VERSION_NUMBER" in error_msg:
            print("  • SSL mismatch detected!")
            print(f"  • Current setting: REDIS_SSL={settings.REDIS_SSL}")
            print("  • Try the opposite setting:")
            print(f"    → Set REDIS_SSL={'False' if settings.REDIS_SSL else 'True'} in .env")
        else:
            print("  1. Check if host/port are correct")
            print(f"     Host: {settings.REDIS_HOST}")
            print(f"     Port: {settings.REDIS_PORT}")
            print("  2. Check firewall/network connectivity")
            print("  3. Verify Redis Cloud database is active")
            print("  4. Check your IP is whitelisted in Redis Cloud")
        
        return False
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auto_detect_ssl():
    """Auto-detect correct SSL setting"""
    print("\n" + "=" * 70)
    print("AUTO-DETECTING SSL SETTING")
    print("=" * 70)
    
    for use_ssl in [False, True]:
        protocol = "SSL" if use_ssl else "Plain"
        print(f"\nTrying {protocol} connection...")
        
        try:
            conn_params = {
                'host': settings.REDIS_HOST,
                'port': settings.REDIS_PORT,
                'db': settings.REDIS_DB,
                'username': settings.REDIS_USERNAME,
                'password': settings.REDIS_PASSWORD,
                'decode_responses': True,
                'socket_connect_timeout': 5,
                'socket_timeout': 5
            }
            
            if use_ssl:
                conn_params['ssl'] = True
                conn_params['ssl_cert_reqs'] = ssl.CERT_NONE
                conn_params['ssl_check_hostname'] = False
            
            r = redis.Redis(**conn_params)
            r.ping()
            
            print(f"  ✓ {protocol} connection successful!")
            print(f"\n✓ CORRECT SETTING: REDIS_SSL={use_ssl}")
            print("\nUpdate your .env file:")
            print(f"  REDIS_SSL={use_ssl}")
            
            return use_ssl
            
        except Exception as e:
            print(f"  ✗ {protocol} failed: {str(e)[:50]}")
    
    print("\n✗ Both SSL and non-SSL failed!")
    print("Check your Redis Cloud credentials and network.")
    return None


if __name__ == "__main__":
    # First try normal test
    success = test_redis_cloud()
    
    # If failed and it's an SSL issue, auto-detect
    if not success:
        print("\n" + "=" * 70)
        input("Press Enter to run auto-detection...")
        detected_ssl = test_auto_detect_ssl()
        
        if detected_ssl is not None:
            print("\n" + "=" * 70)
            print("Run the test again after updating .env")
            print("=" * 70)
    
    sys.exit(0 if success else 1)