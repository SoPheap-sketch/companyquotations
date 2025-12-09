import importlib
import traceback
import sys

print("=== Import test for app.main ===")

try:
    m = importlib.import_module("app.main")
    print("Imported app.main OK")
except Exception:
    print("FAILED to import app.main:")
    traceback.print_exc()
    sys.exit(1)

app = getattr(m, "app", None)
if app is None:
    print("ERROR: app.main does NOT contain variable 'app'")
    sys.exit(1)

print("\n=== Registered routes ===")
for r in app.routes:
    print(" -", getattr(r, "path", str(r)))

print("\nHas debug function _debug_projects_check?:", hasattr(m, "_debug_projects_check"))
