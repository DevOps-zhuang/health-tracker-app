import os
import sqlite3
from app import app, db

# Ensure the instance directory exists
os.makedirs('instance', exist_ok=True)

# Remove the existing database file if it exists
db_path = 'instance/health_tracker.sqlite'
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")
    except Exception as e:
        print(f"Warning: Could not remove existing database: {e}")

# Create new database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

# Verify the database was created correctly
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Database created with tables: {tables}")
    conn.close()
except Exception as e:
    print(f"Error verifying database: {e}")

# Add initial data for testing
with app.app_context():
    from app.models import Person, HealthData
    person1 = Person(name="John Doe", age=30, gender="Male", description="Test person 1")
    person2 = Person(name="Jane Smith", age=25, gender="Female", description="Test person 2")
    db.session.add(person1)
    db.session.add(person2)
    db.session.commit()
    print("Initial data added successfully!")
