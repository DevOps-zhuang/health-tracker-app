import os
import sys
import subprocess
import argparse
import logging
import platform

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VirtualEnvironment:
    """
    Virtual environment manager for the application.
    Handles detection and activation of Python virtual environment.
    """
    
    def __init__(self, base_dir):
        """
        Initialize the virtual environment manager.
        
        Args:
            base_dir (str): The base directory of the application
        """
        self.base_dir = base_dir
        self.venv_dir = os.path.join(base_dir, 'venv')
        self.is_windows = platform.system().lower() == 'windows'
        
    def exists(self):
        """
        Check if a virtual environment exists.
        
        Returns:
            bool: True if virtual environment exists, False otherwise
        """
        return os.path.exists(self.venv_dir)
    
    def get_python_path(self):
        """
        Get the path to the Python executable in the virtual environment.
        
        Returns:
            str: Path to Python executable
        """
        if self.is_windows:
            return os.path.join(self.venv_dir, 'Scripts', 'python.exe')
        else:
            return os.path.join(self.venv_dir, 'bin', 'python')
    
    def get_activate_path(self):
        """
        Get the path to the activation script for the virtual environment.
        
        Returns:
            str: Path to activation script
        """
        if self.is_windows:
            return os.path.join(self.venv_dir, 'Scripts', 'activate.bat')
        else:
            return os.path.join(self.venv_dir, 'bin', 'activate')
            
    def create(self):
        """
        Create a new virtual environment.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.exists():
            logger.info("Virtual environment already exists.")
            return True
            
        try:
            logger.info("Creating virtual environment...")
            # Ensure we're using Python 3.12+
            subprocess.run(
                [sys.executable, '-m', 'venv', self.venv_dir], 
                check=True
            )
            logger.info("Virtual environment created successfully.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {str(e)}")
            return False
    
    def install_requirements(self):
        """
        Install required packages from requirements.txt.
        Ensures Flask 2.33+ is installed.
        
        Returns:
            bool: True if successful, False otherwise
        """
        requirements_path = os.path.join(self.base_dir, 'requirements.txt')
        if not os.path.exists(requirements_path):
            logger.warning("requirements.txt not found. Creating one with Flask 2.33+")
            try:
                with open(requirements_path, 'w') as f:
                    f.write("Flask>=2.33.0\n")
                    f.write("flask-sqlalchemy\n")
                    f.write("flask-login\n")
                    f.write("flask-migrate\n")
                    f.write("python-dotenv\n")
            except Exception as e:
                logger.error(f"Failed to create requirements.txt: {str(e)}")
                return False
            
        try:
            logger.info("Installing required packages...")
            python_path = self.get_python_path()
            
            # Update pip first
            subprocess.run(
                [python_path, '-m', 'pip', 'install', '--upgrade', 'pip'],
                check=True
            )
            
            # Install requirements
            subprocess.run(
                [python_path, '-m', 'pip', 'install', '-r', requirements_path], 
                check=True
            )
            
            # Ensure Flask is at least 2.33
            subprocess.run(
                [python_path, '-m', 'pip', 'install', 'Flask>=2.33.0'], 
                check=True
            )
            
            logger.info("Required packages installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install required packages: {str(e)}")
            return False


class AppStarter:
    """
    Health tracker application starter.
    Provides various startup options including database reset and browser opening.
    """
    
    def __init__(self):
        """Initialize the application starter."""
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.venv = VirtualEnvironment(self.base_dir)
    
    def setup_environment(self):
        """
        Set up the virtual environment for the application.
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        # Create virtual environment if it doesn't exist
        if not self.venv.exists():
            if not self.venv.create():
                return False
                
        # Install required packages
        if not self.venv.install_requirements():
            return False
            
        return True
    
    def reset_database(self):
        """
        Reset the database.
        
        Returns:
            bool: True if reset was successful, False otherwise
        """
        logger.info("Resetting database...")
        try:
            python_path = self.venv.get_python_path() if self.venv.exists() else sys.executable
            result = subprocess.run(
                [python_path, os.path.join(self.base_dir, 'db_manager.py'), 'reset'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("Database reset successfully!")
                logger.debug(result.stdout)
                return True
            else:
                logger.error(f"Database reset failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error running database reset script: {str(e)}")
            return False
    
    def start_app(self, reset_db=False, open_browser=False, setup_venv=True):
        """
        Start the application.
        
        Args:
            reset_db (bool): Whether to reset the database before starting
            open_browser (bool): Whether to open a browser after starting
            setup_venv (bool): Whether to set up the virtual environment
            
        Returns:
            bool: True if start was successful, False otherwise
        """
        # Set up virtual environment if requested
        if setup_venv:
            if not self.setup_environment():
                logger.error("Failed to set up virtual environment. Application not started.")
                return False
        
        # Reset database if requested
        if reset_db:
            if not self.reset_database():
                logger.error("Application not started due to database reset failure.")
                return False
        
        # Build startup command
        python_path = self.venv.get_python_path() if self.venv.exists() else sys.executable
        cmd = [python_path, os.path.join(self.base_dir, 'app.py')]
        if open_browser:
            cmd.append('--browser')
        
        # Start application
        logger.info("Starting application...")
        try:
            process = subprocess.Popen(cmd)
            logger.info(f"Application started with process ID: {process.pid}")
            logger.info("Access at: http://127.0.0.1:5000")
            return True
        except Exception as e:
            logger.error(f"Error starting application: {str(e)}")
            return False


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Health Tracker Application Starter')
    parser.add_argument('--reset', action='store_true', help='Reset database before starting')
    parser.add_argument('--browser', action='store_true', help='Automatically open browser after starting')
    parser.add_argument('--no-venv-setup', action='store_true', help='Skip virtual environment setup')
    args = parser.parse_args()
    
    # Verify Python version
    if sys.version_info < (3, 12):
        logger.warning("This application requires Python 3.12 or higher.")
        logger.warning(f"Current Python version: {sys.version}")
        sys.exit(1)
    
    # Create starter instance and start application
    starter = AppStarter()
    starter.start_app(
        reset_db=args.reset, 
        open_browser=args.browser,
        setup_venv=not args.no_venv_setup
    )

# Generated by Copilot