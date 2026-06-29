"""Debug login - test the full authenticate flow."""
from sqlalchemy import text
from app.core.db import engine
from app.core.security import verify_password


def main():
    with engine.connect() as conn:
        # Get user by username
        result = conn.execute(
            text('SELECT id, username, hashed_password FROM "user" WHERE username = :u'),
            {"u": "admin"}
        )
        row = result.fetchone()
        if not row:
            print("User 'admin' NOT found")
            return

        print(f"User found: id={row[0]}, username={row[1]}")
        stored_hash = row[2]

        # Test password
        ok, new_hash = verify_password("123456", stored_hash)
        print(f"Password '123456' verify: ok={ok}")

        # Also test wrong password
        ok2, _ = verify_password("wrong", stored_hash)
        print(f"Password 'wrong' verify: ok={ok2}")


if __name__ == "__main__":
    main()
