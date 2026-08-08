import re
import glob
from pathlib import Path

FILES = {
    "admin.py":        "app/api/admin.py",
    "schemas.py":       "app/schemas.py",
}
MIGRATION_GLOB = "migrations/versions/*add_admin_users_table*.py"
MODELS_CANDIDATES = ["app/models/admin_user.py"]

def read(path):
    p = Path(path)
    return p.read_text() if p.exists() else None

print("=== 1. Does schemas.py know about AdminUser? ===")
schemas_src = read(FILES["schemas.py"])
if schemas_src is None:
    print(f"  MISSING: {FILES['schemas.py']}")
else:
    hit = re.search(r"class\s+Admin\w*\s*\(", schemas_src)
    print("  Found AdminUser-related schema class." if hit
          else "  No AdminUser schema class found - likely stale, needs one.")

print()
print("=== 2. Do admin.py reference the deleted graph_engine? ===")
for label, path in FILES.items():
    src = read(path)
    if src is None:
        print(f"  MISSING: {path}")
        continue
    bad_imports = re.findall(r"^.*graph_engine.*$", src, re.MULTILINE)
    if bad_imports:
        print(f"  {label}: STALE - references app.graph_engine:")
        for line in bad_imports:
            print(f"      {line.strip()}")
    else:
        print(f"  {label}: clean, no graph_engine references")

print()
print("=== 3. Do admin.py import from app.routing (the live module)? ===")
for label, path in FILES.items():
    src = read(path)
    if src is None:
        continue
    hit = re.search(r"from\s+app\.routing|import\s+app\.routing", src)
    print(f"  {label}: {'imports app.routing' if hit else 'no app.routing import found'}")

print()
print("=== 4. Does a models file define AdminUser matching the migration's columns? ===")
model_src = None
model_path_used = None
for candidate in MODELS_CANDIDATES:
    model_src = read(candidate)
    if model_src is not None:
        model_path_used = candidate
        break

if model_src is None:
    print(f"  MISSING: none of {MODELS_CANDIDATES} found - adjust MODELS_CANDIDATES")
else:
    cls_match = re.search(r"class\s+AdminUser\b.*?(?=\nclass\s|\Z)", model_src, re.DOTALL)
    if not cls_match:
        print(f"  No AdminUser model class found in {model_path_used}")
    else:
        body = cls_match.group(0)
        expected_cols = ["admin_id", "username", "password_hash", "role", "created_at"]
        for col in expected_cols:
            present = col in body
            print(f"  {model_path_used} AdminUser.{col}: {'present' if present else 'MISSING'}")
        if "created_at" in body:
            has_default = re.search(r"created_at.*(server_default|default\s*=)", body, re.DOTALL)
            print("  created_at has a default:", bool(has_default),
                  "(handover flagged this as missing - expect False)")

print()
print("=== 5. Migration sanity: single head, admin_users table present ===")
migration_files = glob.glob(MIGRATION_GLOB)
if not migration_files:
    print(f"  No migration matched {MIGRATION_GLOB} - adjust the glob")
else:
    for mf in migration_files:
        src = read(mf)
        has_table = "admin_users" in src if src else False
        print(f"  {mf}: defines admin_users table = {has_table}")
