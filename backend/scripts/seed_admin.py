"""One-off script to create the first AdminUser account.
Run from backend/: python3 scripts/seed_admin.py
"""
import getpass
import sys

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import AdminUser


def main() -> None:
    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty.", file=sys.stderr)
        sys.exit(1)

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.", file=sys.stderr)
        sys.exit(1)

    role = input("Role [admin]: ").strip() or "admin"

    db = SessionLocal()
    try:
        existing = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing:
            print(f"Username '{username}' already exists.", file=sys.stderr)
            sys.exit(1)

        admin = AdminUser(username=username, password_hash=hash_password(password), role=role)
        db.add(admin)
        db.commit()
        print(f"Created admin '{username}' with role '{role}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
