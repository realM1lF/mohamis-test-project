import sys
sys.path.insert(0, '/app')

print("Python path:", sys.path)
print("CWD:", __import__('os').getcwd())

try:
    from src.tools import ToolRegistry
    print("✅ ToolRegistry OK")
except Exception as e:
    print(f"❌ ToolRegistry FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from src.tools.base import BaseTool
    print("✅ BaseTool OK")
except Exception as e:
    print(f"❌ BaseTool FAILED: {e}")
    import traceback
    traceback.print_exc()
