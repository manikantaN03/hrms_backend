"""
Quick endpoint checker - identifies 500 errors without triggering server reload
"""
import requests
import json
from collections import defaultdict

BASE_URL = "http://localhost:8000"

def check_endpoints():
    """Check all endpoints from OpenAPI spec"""
    
    print("\n" + "="*80)
    print("  HRMS API ENDPOINT HEALTH CHECK")
    print("="*80 + "\n")
    
    # Get OpenAPI spec
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        spec = response.json()
    except Exception as e:
        print(f"❌ Failed to fetch OpenAPI spec: {e}")
        return
    
    paths = spec.get('paths', {})
    
    # Group by tags
    by_tag = defaultdict(list)
    server_errors = []
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                continue
            
            tags = details.get('tags', ['Untagged'])
            tag = tags[0] if tags else 'Untagged'
            
            # Quick test
            url = f"{BASE_URL}{path}"
            try:
                if method.upper() == "GET":
                    r = requests.get(url, timeout=2)
                else:
                    r = requests.request(method.upper(), url, json={}, timeout=2)
                
                status = r.status_code
                
                # Track server errors
                if 500 <= status < 600:
                    server_errors.append({
                        'method': method.upper(),
                        'path': path,
                        'status': status,
                        'tag': tag,
                        'error': r.json() if r.headers.get('content-type', '').startswith('application/json') else r.text[:200]
                    })
                
                by_tag[tag].append({
                    'method': method.upper(),
                    'path': path,
                    'status': status
                })
            except Exception as e:
                by_tag[tag].append({
                    'method': method.upper(),
                    'path': path,
                    'status': 'ERROR',
                    'error': str(e)[:50]
                })
    
    # Print summary by tag
    print(f"📊 Endpoints by Module:\n")
    for tag in sorted(by_tag.keys()):
        endpoints = by_tag[tag]
        errors_5xx = sum(1 for e in endpoints if isinstance(e.get('status'), int) and 500 <= e['status'] < 600)
        errors_4xx = sum(1 for e in endpoints if isinstance(e.get('status'), int) and 400 <= e['status'] < 500)
        success_2xx = sum(1 for e in endpoints if isinstance(e.get('status'), int) and 200 <= e['status'] < 300)
        
        status_icon = "✅" if errors_5xx == 0 else "❌"
        print(f"{status_icon} {tag:30} | Total: {len(endpoints):3} | 2xx: {success_2xx:3} | 4xx: {errors_4xx:3} | 5xx: {errors_5xx:3}")
    
    # Show server errors
    if server_errors:
        print(f"\n{'='*80}")
        print(f"❌ SERVER ERRORS (500) - NEED FIXING: {len(server_errors)} endpoints")
        print(f"{'='*80}\n")
        
        for err in server_errors:
            print(f"❌ {err['method']:6} {err['path']}")
            print(f"   Status: {err['status']}")
            print(f"   Module: {err['tag']}")
            print(f"   Error: {err['error']}")
            print()
        
        # Save to file
        with open('server_errors.json', 'w') as f:
            json.dump(server_errors, f, indent=2)
        print(f"💾 Server errors saved to: server_errors.json\n")
    else:
        print(f"\n{'='*80}")
        print("🎉 NO SERVER ERRORS FOUND! All endpoints are healthy.")
        print(f"{'='*80}\n")
    
    return server_errors

if __name__ == "__main__":
    check_endpoints()
