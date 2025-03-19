import os
import sys
import sqlite3
import shutil
from app import create_app, db
from app.models import User

class DatabaseManager:
    """
    Unified management of database initialization, reset and migration operations
    """
    
    def __init__(self):
        """Initialize the database manager"""
        # Database file paths
        self.basedir = os.path.abspath(os.path.dirname(__file__))
        self.instance_path = os.path.join(self.basedir, 'instance')
        self.db_path = os.path.join(self.instance_path, 'health_tracker.sqlite')
        self.backup_path = self.db_path + '.backup'
        
        # Ensure instance directory exists
        if not os.path.exists(self.instance_path):
            os.makedirs(self.instance_path)
        
        # Create Flask application context
        self.app = create_app()
    
    def create_backup(self):
        """Create database backup"""
        if os.path.exists(self.db_path):
            try:
                shutil.copyfile(self.db_path, self.backup_path)
                print(f"Database backup created successfully: {self.backup_path}")
                return True
            except Exception as e:
                print(f"Error creating backup: {e}")
                return False
        else:
            print("Database file not found, cannot create backup")
            return False
    
    def init_db(self):
        """Initialize database: create table structure without resetting data"""
        # Ensure instance directory exists
        if not os.path.exists(self.instance_path):
            os.makedirs(self.instance_path)
        
        with self.app.app_context():
            db.create_all()
            print("Database tables created successfully!")
        
        # Verify database was created correctly
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Database created successfully with tables: {tables}")
            conn.close()
            return True
        except Exception as e:
            print(f"Error verifying database: {e}")
            return False
    
    def reset_db(self):
        """Reset database: delete old database and create new empty database"""
        print("Starting database reset...")
        
        # Create backup
        if self.create_backup():
            # Delete old database file
            try:
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                    print("Old database deleted")
            except Exception as e:
                print(f"Error deleting old database: {e}")
                return False
        
        # Create new database
        with self.app.app_context():
            db.create_all()
            print("New database created with all tables")
        return True
    
    def migrate_user_id(self):
        """Migrate database: add user_id column and associate existing data"""
        print("Starting database migration...")
        
        # Check if database exists
        if not os.path.exists(self.db_path):
            print(f"Database file not found at {self.db_path}")
            return False
        
        # Create backup
        if not self.create_backup():
            return False
        
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user_id column already exists
            cursor.execute("PRAGMA table_info(health_data)")
            columns = cursor.fetchall()
            columns_dict = {col[1]: col for col in columns}
            
            if 'user_id' not in columns_dict:
                print("Adding user_id column to health_data table...")
                
                # Add user_id column
                cursor.execute("ALTER TABLE health_data ADD COLUMN user_id INTEGER")
                
                # Get the first user (assume existing data will be assigned to the first user)
                with self.app.app_context():
                    first_user = User.query.first()
                    if not first_user:
                        print("No users found in database. Please register a user first.")
                        conn.close()
                        return False
                    user_id = first_user.id
                
                # Update existing health data with user_id
                cursor.execute("UPDATE health_data SET user_id = ?", (user_id,))
                conn.commit()
                print("Migration completed successfully!")
                conn.close()
                return True
            
            else:
                print("Database already has user_id column. No migration needed.")
                conn.close()
                return True
                
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error during migration: {e}")
            print("Database was not modified. Your data is safe.")
            return False


if __name__ == "__main__":
    # Create database manager instance
    db_manager = DatabaseManager()
    
    # Execute different operations based on command line arguments
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action == 'init':
            db_manager.init_db()
            print("Database initialization completed.")
        elif action == 'reset':
            db_manager.reset_db()
            print("Database reset completed.")
        elif action == 'migrate':
            db_manager.migrate_user_id()
            print("Database migration script completed.")
        else:
            print(f"Unknown action: {action}")
            print("Available actions: init, reset, migrate")
    else:
        print("Please specify an action to execute: init, reset, migrate")
        print("Example: python db_manager.py reset")

# Generated by Copilot