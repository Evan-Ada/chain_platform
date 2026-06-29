"""Create test admin user - bypasses ORM to avoid Tag self-reference issue."""
from sqlalchemy import text

from app.core.db import engine
from app.core.security import get_password_hash


def main():
    with engine.begin() as conn:
        # Check if user exists
        result = conn.execute(text("SELECT id FROM \"user\" WHERE username = 'admin'"))
        if result.fetchone():
            print("User 'admin' already exists")
            return

        # Create user directly with raw SQL
        password_hash = get_password_hash("123456")
        conn.execute(
            text(
                "INSERT INTO \"user\" (username, email, password_hash, is_superuser, is_active, full_name, is_active) "
                "VALUES (:username, :email, :password_hash, true, true, :full_name, true)"
            ),
            {"username": "admin", "email": "admin@test.com", "password_hash": password_hash, "full_name": "Admin"},
        )
        print("Created user 'admin' with password '123456'")


if __name__ == "__main__":
    main()
