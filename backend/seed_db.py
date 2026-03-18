import time
from sqlalchemy.exc import OperationalError

from app.core.database import SessionLocal, init_db
from app.models.models import User
from app.core.security import get_password_hash

def seed_admin():
    # 1. Wait for Postgres to be ready (Retry logic)
    # This is crucial for Docker/Kubernetes environments
    db = None
    retries = 5
    while retries > 0:
        try:
            init_db()
            db = SessionLocal()
            print("Database connection established.")
            break
        except OperationalError:
            retries -= 1
            print(f"Database not ready. Retrying in 2s... ({retries} attempts left)")
            time.sleep(2)
    
    if not db:
        print("Could not connect to the database. Exiting.")
        return

    try:
        # 2. Check if admin already exists
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("Admin user already exists. Skipping...")
            return

        # 3. Create the admin user
        new_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("password123"),
            credits=100.0
        )
        
        db.add(new_user)
        db.commit()
        print("Successfully created user: admin with 100 credits.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()