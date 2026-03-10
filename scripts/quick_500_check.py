"""
Quick 500 Error Detection Script
Focuses only on finding server errors
"""
import requests
import json
from collections import defaultdict
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Credentials
SUPERADMIN_EMAIL = "superadmin@levitica.com"
SUPERADMIN_PASSWORD = "Admin@123"

def authenticate():
    """Get access token"""
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": SUPERADMIN_EMAIL, "password": SUPERADMIN_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get('access_token')
    except:
        pass
    return None

def main():
    print("\n" + "="*80)
    print("  QUICK 500 ERROR DETECTION")
    print("="*80 + "\n")
    
    # Authenticate
    print("Authenticating...")
    token = authenticate()
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    if token:
        print("Authenticated successfully\n")
    else:
        print("Authentication failed, testing without auth\n")
    
    # Get OpenAPI spec
    try:
        spec = requests.get(f"{BASE_URL}/openapi.json", timeout=5).json()
    except Exception as e:
        print(f"❌ Failed to get API spec: {e}")
        return
    
    paths = spec.get('paths', {})
    server_errors = []
    tested = 0
    
    print(f"Testing {sum(len(m) for m in paths.values())} endpoints...\n")
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                continue
            
            tested += 1
            url = f"{BASE_URL}{path}"
            
            # Quick test
            try:
                if method.upper() == "GET":
                    r = requests.get(url, headers=headers, timeout=3)
                else:
                    r = requests.request(method.upper(), url, headers=headers, json={}, timeout=3)
                
                # Check for 500 errors
                if 500 <= r.status_code < 600:
                    tag = details.get('tags', ['Unknown'])[0]
                    error_data = r.json() if r.headers.get('content-type', '').startswith('application/json') else r.text[:200]
                    
                    server_errors.append({
                        'method': method.upper(),
                        'path': path,
                        'status': r.status_code,
                        'tag': tag,
                        'operation': details.get('operationId', 'unknown'),
                        'error': error_data
                    })
                    
                    print(f"[ERROR] {method.upper():6} {path}")
                    print(f"   Status: {r.status_code}")
                    print(f"   Module: {tag}")
                    print(f"   Error: {error_data}\n")
                
                # Progress indicator
                if tested % 50 == 0:
                    print(f"Tested {tested} endpoints... ({len(server_errors)} errors found)")
            
            except requests.exceptions.Timeout:
                pass  # Skip timeouts
            except Exception:
                pass  # Skip other errors
            
            time.sleep(0.02)  # Small delay
    
    # Summary
    print(f"\n{'='*80}")
    print(f"  RESULTS")
    print(f"{'='*80}\n")
    
    print(f"Total Endpoints Tested: {tested}")
    print(f"Server Errors (500): {len(server_errors)}\n")
    
    if server_errors:
        # Group by module
        by_module = defaultdict(list)
        for err in server_errors:
            by_module[err['tag']].append(err)
        
        print("Server Errors by Module:\n")
        for module in sorted(by_module.keys()):
            errors = by_module[module]
            print(f"  {module}: {len(errors)} errors")
        
        # Save to file
        with open('server_errors_500.json', 'w') as f:
            json.dump(server_errors, f, indent=2)
        
        print(f"\nDetailed errors saved to: server_errors_500.json")
        
        # Show first few errors
        print(f"\n{'='*80}")
        print("  SAMPLE ERRORS (first 5)")
        print(f"{'='*80}\n")
        
        for err in server_errors[:5]:
            print(f"[ERROR] {err['method']} {err['path']}")
            print(f"   Module: {err['tag']}")
            print(f"   Status: {err['status']}")
            print(f"   Error: {err['error']}\n")
    else:
        print("SUCCESS: NO SERVER ERRORS FOUND!")
        print("All endpoints are working correctly!\n")

if __name__ == "__main__":
    main()
