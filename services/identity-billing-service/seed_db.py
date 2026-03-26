import asyncio
from sqlalchemy.exc import OperationalError
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal, init_db
from app.models.user import User  # Updated import path
from app.core.security import get_password_hash

async def seed_admin():
    # 1. Wait for Postgres to be ready (Retry logic)
    retries = 5
    while retries > 0:
        try:
            # Await the async init_db function
            await init_db()
            print("Database connection established.")
            break
        except Exception as e: # Catching general exceptions as async OperationalError can be wrapped
            retries -= 1
            print(f"Database not ready. Retrying in 2s... ({retries} attempts left) | Error: {e}")
            await asyncio.sleep(2)
    
    if retries == 0:
        print("Could not connect to the database. Exiting.")
        return

    # Use the async context manager for the session
    async with AsyncSessionLocal() as db:
        try:
            # 2. Check if admin already exists (Async query execution)
            result = await db.execute(select(User).filter(User.username == "admin"))
            existing_user = result.scalars().first()
            
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
            await db.commit() # Await the commit
            print("Successfully created user: admin with 100 credits.")
        except Exception as e:
            print(f"Error seeding database: {e}")
            await db.rollback() # Await the rollback

if __name__ == "__main__":
    # Run the async function using asyncio
    asyncio.run(seed_admin())