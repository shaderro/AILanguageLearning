import sys
import os

# Add paths
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
BACKEND_DIR = os.path.join(REPO_ROOT, 'backend')
for p in [REPO_ROOT, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Import the app
from server import app

print("=" * 80)
print("已注册的所有路由:")
print("=" * 80)

for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = ', '.join(route.methods) if route.methods else 'N/A'
        print(f"{methods:10s} {route.path}")

print("\n" + "=" * 80)
print("查找包含 'chat' 的路由:")
print("=" * 80)

chat_routes = [route for route in app.routes if hasattr(route, 'path') and 'chat' in route.path.lower()]
if chat_routes:
    for route in chat_routes:
        methods = ', '.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
        print(f"✅ {methods:10s} {route.path}")
else:
    print("❌ 没有找到包含 'chat' 的路由！") 