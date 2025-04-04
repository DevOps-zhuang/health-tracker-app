import os
import sqlite3
from app import app, db

def migrate_blood_pressure_data():
    """
    This script migrates the database from the old schema (with blood_pressure as a string)
    to the new schema (with separate systolic and diastolic integer fields).
    It preserves all existing data.
    """
    db_path = 'instance/health_tracker.sqlite'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    # Backup the database first
    try:
        from shutil import copyfile
        backup_path = f"{db_path}.backup"
        copyfile(db_path, backup_path)
        print(f"Database backup created at {backup_path}")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the old schema is still in place
        cursor.execute("PRAGMA table_info(health_data)")
        columns = cursor.fetchall()
        columns_dict = {col[1]: col for col in columns}
        
        if 'blood_pressure' in columns_dict and 'systolic' not in columns_dict:
            print("Migrating from old schema to new schema...")
            
            # Get all existing data
            cursor.execute("SELECT id, blood_pressure, heart_rate, tags, timestamp FROM health_data")
            rows = cursor.fetchall()
            
            # Create a temporary table with the new schema
            cursor.execute("""
            CREATE TABLE health_data_new (
                id INTEGER PRIMARY KEY,
                systolic INTEGER NOT NULL,
                diastolic INTEGER NOT NULL,
                heart_rate INTEGER NOT NULL,
                tags TEXT,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Migrate data to the new table
            for row in rows:
                id, blood_pressure, heart_rate, tags, timestamp = row
                
                # Parse blood pressure string (e.g., "120/80")
                try:
                    systolic, diastolic = blood_pressure.split('/')
                    systolic = int(systolic.strip())
                    diastolic = int(diastolic.strip())
                except (ValueError, AttributeError):
                    # If parsing fails, use default values and log the issue
                    print(f"Warning: Could not parse blood pressure value '{blood_pressure}' for ID {id}. Using default values.")
                    systolic = 120
                    diastolic = 80
                
                # Convert heart_rate to integer if it's stored as string
                try:
                    heart_rate = int(heart_rate)
                except (ValueError, TypeError):
                    print(f"Warning: Could not convert heart rate '{heart_rate}' to integer for ID {id}. Using default value.")
                    heart_rate = 70
                
                # Insert into new table
                cursor.execute(
                    "INSERT INTO health_data_new (id, systolic, diastolic, heart_rate, tags, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (id, systolic, diastolic, heart_rate, tags, timestamp)
                )
            
            # Replace the old table with the new one
            cursor.execute("DROP TABLE health_data")
            cursor.execute("ALTER TABLE health_data_new RENAME TO health_data")
            conn.commit()
            print("Migration completed successfully!")
        
        elif 'systolic' in columns_dict and 'diastolic' in columns_dict:
            print("Database already has the new schema. No migration needed.")
        else:
            print("Unexpected database schema. Migration aborted.")
            
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        print("The database was not modified. Your data is safe.")
    finally:
        conn.close()

def migrate_person_data():
    """
    This script migrates the database to include the new Person model.
    It preserves all existing data.
    """
    db_path = 'instance/health_tracker.sqlite'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    # Backup the database first
    try:
        from shutil import copyfile
        backup_path = f"{db_path}.backup"
        copyfile(db_path, backup_path)
        print(f"Database backup created at {backup_path}")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the Person table already exists
        cursor.execute("PRAGMA table_info(person)")
        columns = cursor.fetchall()
        
        if not columns:
            print("Creating Person table...")
            
            # Create the Person table
            cursor.execute("""
            CREATE TABLE person (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                description TEXT
            )
            """)
            
            # Add a foreign key reference to the Person model in the HealthData model
            cursor.execute("PRAGMA table_info(health_data)")
            columns = cursor.fetchall()
            columns_dict = {col[1]: col for col in columns}
            
            if 'person_id' not in columns_dict:
                cursor.execute("""
                CREATE TABLE health_data_new (
                    id INTEGER PRIMARY KEY,
                    person_id INTEGER NOT NULL,
                    systolic INTEGER NOT NULL,
                    diastolic INTEGER NOT NULL,
                    heart_rate INTEGER NOT NULL,
                    tags TEXT,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (person_id) REFERENCES person (id)
                )
                """)
                
                # Migrate data to the new table
                cursor.execute("SELECT id, systolic, diastolic, heart_rate, tags, timestamp FROM health_data")
                rows = cursor.fetchall()
                
                for row in rows:
                    id, systolic, diastolic, heart_rate, tags, timestamp = row
                    person_id = 1  # Default person_id for existing data
                    
                    cursor.execute(
                        "INSERT INTO health_data_new (id, person_id, systolic, diastolic, heart_rate, tags, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (id, person_id, systolic, diastolic, heart_rate, tags, timestamp)
                    )
                
                # Replace the old table with the new one
                cursor.execute("DROP TABLE health_data")
                cursor.execute("ALTER TABLE health_data_new RENAME TO health_data")
                conn.commit()
                print("Person table created and data migrated successfully!")
        
        else:
            print("Person table already exists. No migration needed.")
            
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        print("The database was not modified. Your data is safe.")
    finally:
        conn.close()

if __name__ == "__main__":
    # Run the migrations
    migrate_blood_pressure_data()
    migrate_person_data()
    print("Database migration script completed.")
