"""
Backend Architecture Analyzer
Dynamically analyzes the backend structure and generates real-time statistics
"""

import os
import ast
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import importlib.util
import inspect

logger = logging.getLogger(__name__)


class BackendAnalyzer:
    """Analyzes backend structure and generates comprehensive statistics"""
    
    def __init__(self, base_path: str = "app"):
        self.base_path = Path(base_path)
        self.stats = {
            "models": {},
            "endpoints": {},
            "services": {},
            "repositories": {},
            "modules": {},
            "total_counts": {},
            "last_updated": None
        }
    
    def analyze_all(self) -> Dict[str, Any]:
        """Perform complete backend analysis"""
        try:
            logger.info("🔍 Starting comprehensive backend analysis...")
            
            # Analyze different components
            self.analyze_models()
            self.analyze_endpoints()
            self.analyze_services()
            self.analyze_repositories()
            self.analyze_modules()
            self.calculate_totals()
            
            # Set last updated timestamp
            from datetime import datetime
            self.stats["last_updated"] = datetime.now().isoformat()
            
            logger.info("✅ Backend analysis completed successfully")
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Backend analysis failed: {e}")
            return self.get_fallback_stats()
    
    def analyze_models(self):
        """Analyze database models"""
        models_path = self.base_path / "models"
        if not models_path.exists():
            return
        
        model_categories = {
            "HR & Employee": [],
            "Attendance & Time": [],
            "Payroll & Compensation": [],
            "Statutory & Tax": [],
            "Leave & Request": [],
            "Business & Organization": [],
            "Reports & Analytics": [],
            "Other Domains": []
        }
        
        model_files = list(models_path.glob("*.py"))
        model_files = [f for f in model_files if f.name != "__init__.py"]
        
        for model_file in model_files:
            try:
                models_in_file = self.extract_models_from_file(model_file)
                category = self.categorize_model_file(model_file.name)
                model_categories[category].extend(models_in_file)
            except Exception as e:
                logger.warning(f"Failed to analyze model file {model_file}: {e}")
        
        self.stats["models"] = {
            "categories": model_categories,
            "total_files": len(model_files),
            "total_models": sum(len(models) for models in model_categories.values())
        }
    
    def extract_models_from_file(self, file_path: Path) -> List[str]:
        """Extract model class names from a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            models = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's likely a SQLAlchemy model
                    if any(base.id == 'Base' if isinstance(base, ast.Name) else False 
                          for base in node.bases):
                        models.append(node.name)
                    elif any('Model' in base.id if isinstance(base, ast.Name) else False 
                            for base in node.bases):
                        models.append(node.name)
            
            return models
        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return []
    
    def categorize_model_file(self, filename: str) -> str:
        """Categorize model file based on filename"""
        filename_lower = filename.lower()
        
        if any(keyword in filename_lower for keyword in ['employee', 'onboarding', 'separation']):
            return "HR & Employee"
        elif any(keyword in filename_lower for keyword in ['attendance', 'shift', 'work']):
            return "Attendance & Time"
        elif any(keyword in filename_lower for keyword in ['payroll', 'salary']):
            return "Payroll & Compensation"
        elif any(keyword in filename_lower for keyword in ['tax', 'tds', 'epf', 'esi', 'form16']):
            return "Statutory & Tax"
        elif any(keyword in filename_lower for keyword in ['leave', 'request', 'compoff']):
            return "Leave & Request"
        elif any(keyword in filename_lower for keyword in ['business', 'department', 'location']):
            return "Business & Organization"
        elif any(keyword in filename_lower for keyword in ['report', 'analytics']):
            return "Reports & Analytics"
        else:
            return "Other Domains"
    
    def analyze_endpoints(self):
        """Analyze API endpoints"""
        endpoints_path = self.base_path / "api" / "v1" / "endpoints"
        if not endpoints_path.exists():
            return
        
        endpoint_files = list(endpoints_path.glob("*.py"))
        endpoint_files = [f for f in endpoint_files if f.name != "__init__.py"]
        
        endpoint_categories = defaultdict(list)
        total_routes = 0
        
        for endpoint_file in endpoint_files:
            try:
                routes = self.extract_routes_from_file(endpoint_file)
                total_routes += len(routes)
                category = self.categorize_endpoint_file(endpoint_file.name)
                endpoint_categories[category].append({
                    "file": endpoint_file.name,
                    "routes": len(routes),
                    "methods": routes
                })
            except Exception as e:
                logger.warning(f"Failed to analyze endpoint file {endpoint_file}: {e}")
        
        self.stats["endpoints"] = {
            "categories": dict(endpoint_categories),
            "total_files": len(endpoint_files),
            "total_routes": total_routes
        }
    
    def extract_routes_from_file(self, file_path: Path) -> List[Dict[str, str]]:
        """Extract route information from endpoint file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            routes = []
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('@router.'):
                    # Extract HTTP method and path
                    if '(' in line:
                        method_part = line.split('(')[0].replace('@router.', '')
                        path_part = ""
                        if '"' in line:
                            path_part = line.split('"')[1]
                        elif "'" in line:
                            path_part = line.split("'")[1]
                        
                        routes.append({
                            "method": method_part.upper(),
                            "path": path_part
                        })
            
            return routes
        except Exception as e:
            logger.warning(f"Failed to parse routes from {file_path}: {e}")
            return []
    
    def categorize_endpoint_file(self, filename: str) -> str:
        """Categorize endpoint file based on filename"""
        filename_lower = filename.lower().replace('.py', '')
        
        category_mapping = {
            'auth': 'Authentication',
            'registration': 'User Management',
            'employees': 'Employee Management',
            'allemployees': 'Employee Management',
            'attendance': 'Attendance & Time',
            'payroll': 'Payroll & Compensation',
            'requests': 'Request Management',
            'hrmanagement': 'HR Operations',
            'onboarding': 'Employee Lifecycle',
            'separation': 'Employee Lifecycle',
            'datacapture': 'Data Operations',
            'bulkupdate': 'Data Operations',
            'reports': 'Reports & Analytics',
            'dashboard': 'Dashboard & Stats',
            'setup': 'System Configuration',
            'master_setup': 'System Configuration',
            'business': 'Business Management',
            'crm': 'CRM & Projects',
            'project_management': 'CRM & Projects'
        }
        
        return category_mapping.get(filename_lower, 'Other Operations')
    
    def analyze_services(self):
        """Analyze service files"""
        services_path = self.base_path / "services"
        if not services_path.exists():
            return
        
        service_files = list(services_path.glob("*.py"))
        service_files = [f for f in service_files if f.name != "__init__.py"]
        
        service_categories = defaultdict(list)
        
        for service_file in service_files:
            category = self.categorize_service_file(service_file.name)
            service_categories[category].append(service_file.name)
        
        self.stats["services"] = {
            "categories": dict(service_categories),
            "total_files": len(service_files)
        }
    
    def categorize_service_file(self, filename: str) -> str:
        """Categorize service file based on filename"""
        filename_lower = filename.lower().replace('_service.py', '').replace('.py', '')
        
        if any(keyword in filename_lower for keyword in ['auth', 'registration', 'user']):
            return "Authentication & User"
        elif any(keyword in filename_lower for keyword in ['employee', 'onboarding', 'separation']):
            return "Employee Management"
        elif any(keyword in filename_lower for keyword in ['attendance', 'shift', 'roster']):
            return "Attendance & Time"
        elif any(keyword in filename_lower for keyword in ['payroll', 'salary']):
            return "Payroll & Compensation"
        elif any(keyword in filename_lower for keyword in ['tax', 'tds', 'statutory']):
            return "Statutory & Tax"
        elif any(keyword in filename_lower for keyword in ['leave', 'approval', 'request']):
            return "Leave & Requests"
        elif any(keyword in filename_lower for keyword in ['business', 'department', 'location']):
            return "Business Management"
        else:
            return "Other Services"
    
    def analyze_repositories(self):
        """Analyze repository files"""
        repos_path = self.base_path / "repositories"
        if not repos_path.exists():
            return
        
        repo_files = list(repos_path.glob("*.py"))
        repo_files = [f for f in repo_files if f.name != "__init__.py"]
        
        repo_categories = defaultdict(list)
        
        for repo_file in repo_files:
            category = self.categorize_repository_file(repo_file.name)
            repo_categories[category].append(repo_file.name)
        
        self.stats["repositories"] = {
            "categories": dict(repo_categories),
            "total_files": len(repo_files)
        }
    
    def categorize_repository_file(self, filename: str) -> str:
        """Categorize repository file based on filename"""
        filename_lower = filename.lower().replace('_repository.py', '').replace('.py', '')
        
        if any(keyword in filename_lower for keyword in ['user', 'auth']):
            return "User & Auth"
        elif any(keyword in filename_lower for keyword in ['employee']):
            return "Employee Management"
        elif any(keyword in filename_lower for keyword in ['attendance', 'shift']):
            return "Attendance & Time"
        elif any(keyword in filename_lower for keyword in ['payroll', 'salary']):
            return "Payroll & Compensation"
        elif any(keyword in filename_lower for keyword in ['tax', 'tds', 'statutory']):
            return "Statutory & Tax"
        elif any(keyword in filename_lower for keyword in ['leave', 'approval']):
            return "Leave & Requests"
        elif any(keyword in filename_lower for keyword in ['business', 'department']):
            return "Business Management"
        else:
            return "Other Repositories"
    
    def analyze_modules(self):
        """Analyze core modules"""
        modules = {
            "Core": ["config", "database", "security", "redis_client", "session", "otp"],
            "API": ["router", "deps", "middleware"],
            "Models": ["base", "associations"],
            "Utils": ["business_unit_utils", "helpers"],
            "Schemas": ["base_schemas", "enums"],
            "Exceptions": ["base", "business_exceptions", "http_exceptions"]
        }
        
        existing_modules = {}
        for category, module_list in modules.items():
            existing = []
            for module in module_list:
                # Check if module file exists
                possible_paths = [
                    self.base_path / "core" / f"{module}.py",
                    self.base_path / "api" / "v1" / f"{module}.py",
                    self.base_path / "models" / f"{module}.py",
                    self.base_path / "utils" / f"{module}.py",
                    self.base_path / "schemas" / f"{module}.py",
                    self.base_path / "exceptions" / f"{module}.py",
                    self.base_path / f"{module}.py"
                ]
                
                if any(path.exists() for path in possible_paths):
                    existing.append(module)
            
            if existing:
                existing_modules[category] = existing
        
        self.stats["modules"] = {
            "categories": existing_modules,
            "total_categories": len(existing_modules)
        }
    
    def calculate_totals(self):
        """Calculate total counts for dashboard"""
        self.stats["total_counts"] = {
            "models": self.stats.get("models", {}).get("total_models", 0),
            "endpoints": self.stats.get("endpoints", {}).get("total_files", 0),
            "services": self.stats.get("services", {}).get("total_files", 0),
            "repositories": self.stats.get("repositories", {}).get("total_files", 0),
            "services_and_repos": (
                self.stats.get("services", {}).get("total_files", 0) + 
                self.stats.get("repositories", {}).get("total_files", 0)
            ),
            "core_modules": len(self.stats.get("modules", {}).get("categories", {}))
        }
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """Return fallback statistics if analysis fails"""
        return {
            "models": {"total_models": 59, "categories": {}},
            "endpoints": {"total_files": 52, "categories": {}},
            "services": {"total_files": 73, "categories": {}},
            "repositories": {"total_files": 67, "categories": {}},
            "modules": {"categories": {}, "total_categories": 8},
            "total_counts": {
                "models": 59,
                "endpoints": 52,
                "services": 73,
                "repositories": 67,
                "services_and_repos": 140,
                "core_modules": 8
            },
            "last_updated": None,
            "error": "Analysis failed, using fallback data"
        }


# Global analyzer instance
analyzer = BackendAnalyzer()


def get_backend_stats() -> Dict[str, Any]:
    """Get current backend statistics"""
    return analyzer.analyze_all()


def get_cached_stats() -> Dict[str, Any]:
    """Get cached statistics (for performance)"""
    if not analyzer.stats.get("last_updated"):
        return analyzer.analyze_all()
    return analyzer.stats


if __name__ == "__main__":
    # Test the analyzer
    stats = get_backend_stats()
    print(json.dumps(stats, indent=2))