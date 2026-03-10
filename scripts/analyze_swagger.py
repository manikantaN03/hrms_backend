"""
Analyze Swagger/OpenAPI spec and identify potential issues
"""
import requests
import json
from collections import defaultdict

BASE_URL = "http://localhost:8000"

def main():
    print("\n" + "="*80)
    print("  SWAGGER API ANALYSIS")
    print("="*80 + "\n")
    
    # Get OpenAPI spec
    try:
        print("Fetching OpenAPI specification...")
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        spec = response.json()
        print("Success!\n")
    except Exception as e:
        print(f"ERROR: Failed to fetch OpenAPI spec: {e}\n")
        return
    
    paths = spec.get('paths', {})
    
    # Analyze endpoints
    print(f"Total API paths: {len(paths)}")
    
    # Group by tags/modules
    by_tag = defaultdict(list)
    total_endpoints = 0
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                continue
            
            total_endpoints += 1
            tags = details.get('tags', ['Untagged'])
            tag = tags[0] if tags else 'Untagged'
            
            by_tag[tag].append({
                'method': method.upper(),
                'path': path,
                'operation_id': details.get('operationId', 'unknown'),
                'summary': details.get('summary', ''),
                'parameters': details.get('parameters', []),
                'requestBody': details.get('requestBody', {}),
                'responses': details.get('responses', {})
            })
    
    print(f"Total endpoints: {total_endpoints}\n")
    
    # Print module summary
    print("="*80)
    print("  MODULES/TAGS SUMMARY")
    print("="*80 + "\n")
    
    for tag in sorted(by_tag.keys()):
        endpoints = by_tag[tag]
        print(f"{tag:40} | {len(endpoints):3} endpoints")
    
    # Identify endpoints with potential issues
    print(f"\n{'='*80}")
    print("  POTENTIAL ISSUES")
    print(f"{'='*80}\n")
    
    issues_found = False
    
    # Check for endpoints with path parameters but no validation
    for tag, endpoints in by_tag.items():
        for endpoint in endpoints:
            path = endpoint['path']
            
            # Check for path parameters
            if '{' in path:
                param_names = [p.split('}')[0] for p in path.split('{')[1:]]
                
                # Check if parameters are documented
                documented_params = [p['name'] for p in endpoint['parameters'] if p.get('in') == 'path']
                
                missing_docs = set(param_names) - set(documented_params)
                if missing_docs:
                    issues_found = True
                    print(f"[WARNING] {endpoint['method']} {path}")
                    print(f"  Module: {tag}")
                    print(f"  Missing parameter documentation: {missing_docs}")
                    print()
    
    if not issues_found:
        print("No obvious issues found in API specification.\n")
    
    # Save full spec analysis
    analysis = {
        'total_paths': len(paths),
        'total_endpoints': total_endpoints,
        'modules': {tag: len(endpoints) for tag, endpoints in by_tag.items()},
        'endpoints_by_module': {tag: [{'method': e['method'], 'path': e['path'], 'operation_id': e['operation_id']} for e in endpoints] for tag, endpoints in by_tag.items()}
    }
    
    with open('swagger_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"Full analysis saved to: swagger_analysis.json\n")
    
    # Print list of all endpoints for manual testing
    print("="*80)
    print("  ALL ENDPOINTS (for manual testing in Swagger UI)")
    print("="*80 + "\n")
    print(f"Open Swagger UI at: {BASE_URL}/docs\n")
    
    for tag in sorted(by_tag.keys()):
        print(f"\n{tag}:")
        for endpoint in by_tag[tag][:5]:  # Show first 5 per module
            print(f"  {endpoint['method']:6} {endpoint['path']}")
        if len(by_tag[tag]) > 5:
            print(f"  ... and {len(by_tag[tag]) - 5} more")

if __name__ == "__main__":
    main()
