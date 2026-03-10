"""
API Routes Listing
Displays all available endpoints
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.main import app


def list_routes():
    """Display all API routes."""
    
    print("\n" + "=" * 80)
    print("AVAILABLE API ROUTES")
    print("=" * 80)
    
    # Collect all routes
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            for method in route.methods:
                if method != "HEAD":  # Exclude HEAD requests
                    routes.append((method, route.path))
    
    # Sort by path
    routes.sort(key=lambda x: x[1])
    
    # Display routes
    print(f"\n{'Method':<10} {'Path':<60}")
    print("-" * 80)
    
    for method, path in routes:
        print(f"{method:<10} {path:<60}")
    
    print("-" * 80)
    print(f"\nTotal routes: {len(routes)}")
    print("=" * 80)
    
    # Group by tags
    print("\nRoutes by Category:")
    print("-" * 80)
    
    categories = {}
    for route in app.routes:
        if hasattr(route, 'tags') and route.tags:
            tag = route.tags[0]
            if tag not in categories:
                categories[tag] = []
            categories[tag].append(route.path)
    
    for tag, paths in sorted(categories.items()):
        print(f"\n{tag}:")
        for path in sorted(set(paths)):
            print(f"  {path}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    list_routes()