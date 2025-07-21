#!/usr/bin/env python3
"""
Comprehensive audit script for MediTwin Agents Backend endpoints.
This validates the endpoint structure and implementation without starting the server.
"""

import os
import ast
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def audit_endpoint_file(file_path):
    """Audit a single endpoint file and extract route information."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        routes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if (isinstance(decorator, ast.Attribute) and 
                        isinstance(decorator.value, ast.Name) and 
                        decorator.value.id == 'router'):
                        
                        method = decorator.attr
                        route_path = "/"  # default
                        
                        # Extract path from decorator arguments
                        if hasattr(decorator, 'args') and len(decorator.args) > 0:
                            pass  # Complex parsing needed for this
                        
                        routes.append({
                            'method': method,
                            'function': node.name,
                            'path': route_path,
                            'line': node.lineno
                        })
        
        return routes
    except Exception as e:
        return [{'error': str(e)}]

def main():
    """Main audit function."""
    print("🔍 MediTwin Agents Backend Endpoint Audit")
    print("=" * 50)
    
    endpoints_dir = Path("src/api/v1/endpoints")
    
    if not endpoints_dir.exists():
        print("❌ Endpoints directory not found")
        return
    
    endpoint_files = list(endpoints_dir.glob("*.py"))
    endpoint_files = [f for f in endpoint_files if f.name != "__init__.py"]
    
    print(f"📁 Found {len(endpoint_files)} endpoint files")
    print()
    
    total_routes = 0
    
    for file_path in sorted(endpoint_files):
        print(f"📄 {file_path.name}")
        print("-" * 40)
        
        routes = audit_endpoint_file(file_path)
        
        if routes:
            if routes and 'error' in routes[0]:
                print(f"   ⚠️  Could not parse: {routes[0].get('error', 'Unknown error')}")
            else:
                for route in routes:
                    if 'error' not in route:
                        print(f"   {route['method'].upper():6} {route['function']}")
                        total_routes += 1
        else:
            print("   📭 No routes found")
        
        print()
    
    print(f"📊 Summary: {total_routes} routes found across {len(endpoint_files)} files")
    
    # Verify key requirements
    print("\n🎯 Key Requirements Verification")
    print("-" * 40)
    
    required_files = [
        "admin.py",       # Admin endpoints
        "anatomy.py",     # Body parts & regions  
        "chat.py",        # Basic chat
        "expert_opinion.py",  # Expert consultation
        "timeline.py",    # Timeline & history
        "export.py",      # PDF export
        "documents.py",   # Document upload/processing
        "upload.py",      # File upload
        "events.py",      # Manual events
    ]
    
    existing_files = [f.name for f in endpoint_files]
    
    for req_file in required_files:
        if req_file in existing_files:
            print(f"   ✅ {req_file}")
        else:
            print(f"   ❌ {req_file} - MISSING")
    
    # Check configuration files
    print("\n⚙️  Configuration Files")
    print("-" * 40)
    
    config_files = [
        "src/config/body_regions.py",
        "src/utils/report_generator.py",
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"   ✅ {config_file}")
        else:
            print(f"   ❌ {config_file} - MISSING")
    
    # Router configuration check
    print("\n🔗 Router Configuration")
    print("-" * 40)
    
    try:
        with open("src/api/v1/router.py", 'r') as f:
            router_content = f.read()
        
        required_routers = [
            "export", "timeline", "anatomy", "chat", "expert_opinion", 
            "admin", "documents", "upload"
        ]
        
        for router_name in required_routers:
            if f'prefix="/{router_name}"' in router_content or f"prefix=\"/{router_name}\"" in router_content:
                print(f"   ✅ /{router_name}")
            else:
                print(f"   ❌ /{router_name} - NOT REGISTERED")
                
    except Exception as e:
        print(f"   ⚠️  Could not check router configuration: {e}")

if __name__ == "__main__":
    main()
