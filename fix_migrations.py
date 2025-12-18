from sqlalchemy import create_engine, text
import os

# 1. Update this with your Railway External Database URL 
# (Find it in Railway under PostgreSQL -> Variables -> DATABASE_URL or Connection -> External URL)
DATABASE_URL = "postgresql://postgres:IwIPQJHldYgDFfXimwwEQVIvkPbAIlnV@switchback.proxy.rlwy.net:50961/railway"

def reset_database():
    if not DATABASE_URL or "your_user" in DATABASE_URL:
        print("ERROR: You must provide your actual DATABASE_URL in the script.")
        return

    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            print("Connecting to Railway...")
            
            # This is the "Nuclear" SQL command for Postgres
            # It drops everything and rebuilds the basic public schema
            print("Wiping existing schema and all tables...")
            
            # Start a transaction block
            trans = connection.begin()
            try:
                connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
                connection.execute(text("CREATE SCHEMA public;"))
                connection.execute(text("GRANT ALL ON SCHEMA public TO public;"))
                connection.execute(text("GRANT ALL ON SCHEMA public TO postgres;")) # Standard permission
                trans.commit()
                print("SUCCESS: Database is now completely empty.")
            except Exception as e:
                trans.rollback()
                raise e

        print("\n--- NEXT STEPS ---")
        print("1. Run: rm -rf migrations (or delete the folder manually)")
        print("2. Run: flask db init")
        print("3. Run: flask db migrate -m 'Initial Start'")
        print("4. Push to Railway")
        
    except Exception as e:
        print(f"\nFAILED: {e}")

if __name__ == "__main__":
    reset_database()