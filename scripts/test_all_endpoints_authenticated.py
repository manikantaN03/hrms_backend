"""
Comprehensive API Endpoint Testing with Authentication
Tests all endpoints and identifies 500 errors
"""
import requests
import json
from collections import defaultdict
from typing import Dict, List, Optional
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Credentials
SUPERADMIN_EMAIL = "superadmin@levitica.com"
SUPERADMIN_PASSWORD = "Admin@123"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class EndpointTester:
    def __init__(self):
        self.access_token = None
        self.headers = {}
        self.results = {
            'success': [],
            'client_error': [],
            'server_error': [],
            'connection_error': []
        }
    
    def authenticate(self) -> bool:
        """Authenticate and get access token"""
        print(f"\n{Colors.CYAN}🔐 Authenticating as Superadmin...{Colors.RESET}")
        
        try:
            response = requests.post(
                f"{API_BASE}/auth/login",
                json={
                    "email": SUPERADMIN_EMAIL,
                    "password": SUPERADMIN_PASSWORD
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
                print(f"{Colors.GREEN}✓ Authentication successful!{Colors.RESET}\n")
                return True
            else:
                print(f"{Colors.RED}✗ Authentication failed: {response.status_code} {response.text}{Colors.RESET}\n")
                return False
        except Exception as e:
            print(f"{Colors.RED}✗ Authentication error: {e}{Colors.RESET}\n")
            return False
    
    def test_endpoint(self, method: str, path: str, use_auth: bool = True) -> Dict:
        """Test a single endpoint"""
        url = f"{BASE_URL}{path}"
        headers = self.headers if use_auth else {}
        
        result = {
            'method': method.upper(),
            'path': path,
            'status': 0,
            'reason': '',
            'response': None,
            'error': None
        }
        
        try:
            # Prepare request based on method
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json={}, timeout=5)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json={}, timeout=5)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=5)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json={}, timeout=5)
            else:
                result['reason'] = 'UNSUPPORTED_METHOD'
                return result
            
            result['status'] = response.status_code
            result['reason'] = response.reason
            
            # Try to parse JSON response
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    result['response'] = response.json()
                except:
                    result['response'] = response.text[:200]
            else:
                result['response'] = response.text[:200] if response.text else None
            
        except requests.exceptions.Timeout:
            result['reason'] = 'TIMEOUT'
            result['error'] = 'Request timed out'
        except requests.exceptions.ConnectionError:
            result['reason'] = 'CONNECTION_ERROR'
            result['error'] = 'Failed to connect to server'
        except Exception as e:
            result['reason'] = 'EXCEPTION'
            result['error'] = str(e)
        
        return result
    
    def categorize_result(self, result: Dict, tag: str):
        """Categorize test result"""
        status = result['status']
        
        result['tag'] = tag
        
        if status == 0:
            self.results['connection_error'].append(result)
        elif 200 <= status < 300:
            self.results['success'].append(result)
        elif 400 <= status < 500:
            self.results['client_error'].append(result)
        elif 500 <= status < 600:
            self.results['server_error'].append(result)
    
    def print_result(self, result: Dict):
        """Print test result with color coding"""
        status = result['status']
        method = result['method']
        path = result['path']
        
        if status == 0:
            print(f"  {Colors.RED}✗ ERROR: {result['reason']}{Colors.RESET}")
            if result['error']:
                print(f"    {result['error']}")
        elif 200 <= status < 300:
            print(f"  {Colors.GREEN}✓ {status} {result['reason']}{Colors.RESET}")
        elif 400 <= status < 500:
            print(f"  {Colors.YELLOW}⚠ {status} {result['reason']}{Colors.RESET}")
        elif 500 <= status < 600:
            print(f"  {Colors.RED}✗ {status} {result['reason']} - SERVER ERROR!{Colors.RESET}")
            if result['response']:
                error_detail = result['response'].get('detail', result['response']) if isinstance(result['response'], dict) else result['response']
                print(f"    {Colors.RED}Error: {error_detail}{Colors.RESET}")
    
    def test_all_endpoints(self):
        """Test all endpoints from OpenAPI spec"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}")
        print(f"  HRMS API COMPREHENSIVE ENDPOINT TESTING")
        print(f"{'='*80}{Colors.RESET}\n")
        
        # Get OpenAPI spec
        try:
            response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
            spec = response.json()
        except Exception as e:
            print(f"{Colors.RED}Failed to fetch OpenAPI spec: {e}{Colors.RESET}")
            return
        
        paths = spec.get('paths', {})
        total_endpoints = sum(len([m for m in methods.keys() if m.lower() in ['get', 'post', 'put', 'delete', 'patch']]) for methods in paths.values())
        
        print(f"{Colors.CYAN}📊 Found {total_endpoints} endpoints to test{Colors.RESET}\n")
        
        # Group by tags for organized testing
        by_tag = defaultdict(list)
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                    continue
                
                tags = details.get('tags', ['Untagged'])
                tag = tags[0] if tags else 'Untagged'
                operation_id = details.get('operationId', 'unknown')
                
                by_tag[tag].append({
                    'method': method,
                    'path': path,
                    'operation_id': operation_id,
                    'summary': details.get('summary', '')
                })
        
        # Test endpoints by tag
        for tag in sorted(by_tag.keys()):
            endpoints = by_tag[tag]
            print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'─'*80}")
            print(f"📦 Module: {tag} ({len(endpoints)} endpoints)")
            print(f"{'─'*80}{Colors.RESET}\n")
            
            for endpoint in endpoints:
                method = endpoint['method']
                path = endpoint['path']
                operation_id = endpoint['operation_id']
                
                print(f"{Colors.CYAN}{method.upper():6}{Colors.RESET} {path}")
                if endpoint['summary']:
                    print(f"  {Colors.BLUE}→ {endpoint['summary']}{Colors.RESET}")
                
                # Determine if endpoint needs authentication
                # Public endpoints (no auth needed)
                public_paths = [
                    '/favicon.ico',
                    '/backend-stats',
                    '/api/backend-stats',
                    '/',
                    '/health',
                    '/api/v1/register',
                    '/api/v1/verify-otp',
                    '/api/v1/resend-otp',
                    '/api/v1/set-password',
                    '/api/v1/auth/login',
                    '/api/v1/contact-inquiry',
                    '/api/v1/public',
                    '/api/v1/forgot-password',
                    '/api/v1/reset-password',
                    '/api/v1/password-reset'
                ]
                
                use_auth = not any(path.startswith(p) for p in public_paths)
                
                # Test the endpoint
                result = self.test_endpoint(method, path, use_auth)
                self.categorize_result(result, tag)
                self.print_result(result)
                print()
                
                time.sleep(0.05)  # Small delay to avoid overwhelming the server
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}")
        print(f"  TEST SUMMARY")
        print(f"{'='*80}{Colors.RESET}\n")
        
        total = sum(len(v) for v in self.results.values())
        success_count = len(self.results['success'])
        client_error_count = len(self.results['client_error'])
        server_error_count = len(self.results['server_error'])
        connection_error_count = len(self.results['connection_error'])
        
        print(f"📊 Total Endpoints Tested: {total}")
        print(f"{Colors.GREEN}✓ Success (2xx):{Colors.RESET} {success_count} ({success_count/total*100:.1f}%)")
        print(f"{Colors.YELLOW}⚠ Client Errors (4xx):{Colors.RESET} {client_error_count} ({client_error_count/total*100:.1f}%) - Expected (need auth/data)")
        print(f"{Colors.RED}✗ Server Errors (5xx):{Colors.RESET} {server_error_count} ({server_error_count/total*100:.1f}%)")
        print(f"{Colors.RED}✗ Connection Errors:{Colors.RESET} {connection_error_count}")
        
        # Show server errors in detail
        if self.results['server_error']:
            print(f"\n{Colors.BOLD}{Colors.RED}{'='*80}")
            print(f"  ❌ SERVER ERRORS (500) - NEED IMMEDIATE FIXING")
            print(f"{'='*80}{Colors.RESET}\n")
            
            # Group by tag
            by_tag = defaultdict(list)
            for error in self.results['server_error']:
                by_tag[error['tag']].append(error)
            
            for tag in sorted(by_tag.keys()):
                errors = by_tag[tag]
                print(f"\n{Colors.MAGENTA}📦 {tag} - {len(errors)} errors{Colors.RESET}\n")
                
                for error in errors:
                    print(f"{Colors.RED}✗ {error['method']:6} {error['path']}{Colors.RESET}")
                    print(f"  Status: {error['status']} {error['reason']}")
                    if error['response']:
                        if isinstance(error['response'], dict):
                            detail = error['response'].get('detail', error['response'])
                            print(f"  Error: {json.dumps(detail, indent=2)}")
                        else:
                            print(f"  Error: {error['response']}")
                    print()
            
            # Save to file
            with open('server_errors_detailed.json', 'w') as f:
                json.dump(self.results['server_error'], f, indent=2)
            
            print(f"{Colors.CYAN}💾 Detailed server errors saved to: server_errors_detailed.json{Colors.RESET}")
        else:
            print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*80}")
            print(f"  🎉 NO SERVER ERRORS FOUND!")
            print(f"  All endpoints are working correctly!")
            print(f"{'='*80}{Colors.RESET}")
        
        # Save all results
        with open('endpoint_test_results_full.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n{Colors.CYAN}💾 Full test results saved to: endpoint_test_results_full.json{Colors.RESET}\n")

def main():
    tester = EndpointTester()
    
    # Authenticate first
    if not tester.authenticate():
        print(f"{Colors.RED}Cannot proceed without authentication. Please check credentials.{Colors.RESET}")
        return
    
    # Test all endpoints
    tester.test_all_endpoints()

if __name__ == "__main__":
    main()
