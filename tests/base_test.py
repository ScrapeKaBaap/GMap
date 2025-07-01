import unittest
import os
import atexit
import signal
import sys
import asyncio

# Import module functions - ensure they are designed to be called externally
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.config_manager import ConfigManager
from modules.database_manager import DatabaseManager

class BaseTestMixin:
    """Mixin class with common test functionality that can be shared between sync and async tests."""
    
    def _common_setup(self):
        """Common setup logic for both sync and async tests."""
        # Track test files for cleanup
        self._test_files_to_cleanup = []
        
        # Setup test directory
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.test_dir, "test_config.ini")
        self.db_file = os.path.join(self.test_dir, "test_database.db")
        
        # Save original working directory
        self.original_cwd = os.getcwd()
        
        # Register cleanup handlers for interrupted tests
        self._register_cleanup_handlers()
        
        # Create test config file
        self._create_test_config()
        
        # Change to test directory
        os.chdir(self.test_dir)
        
        # Initialize managers
        self.config_manager = ConfigManager(config_file="test_config.ini")
        self.db_manager = DatabaseManager(config_manager=self.config_manager)
        
        # Add files to cleanup list
        self._test_files_to_cleanup.extend([self.config_file, self.db_file])
    
    def _create_test_config(self):
        """Create the test configuration file."""
        config_content = self._get_test_config_content()
        with open(self.config_file, "w") as f:
            f.write(config_content)
    
    def _get_test_config_content(self):
        """Get the default test configuration content. Override in subclasses if needed."""
        return """[TestSection]
key1 = value1
key2 = 123
key3 = True

[Search]
search_query_templates = tech companies in ${country}
country = Australia
max_companies_per_query = 5

[Database]
db_name = test_database.db

[Playwright]
headless = True

[Tests]
delete_test_config = True
delete_test_db = False
test_config_name = test_config.ini
test_db_name = test_database.db
"""
    
    def _register_cleanup_handlers(self):
        """Register cleanup handlers for interrupted tests (Ctrl+C, etc)."""
        # Register atexit handler
        atexit.register(self._sync_emergency_cleanup)
        
        # Register signal handlers for common interruption signals
        signal.signal(signal.SIGINT, self._signal_cleanup_handler)
        signal.signal(signal.SIGTERM, self._signal_cleanup_handler)
    
    def _signal_cleanup_handler(self, signum, frame):
        """Handle cleanup when test is interrupted by signal."""
        print(f"\nReceived signal {signum}, cleaning up test files...")
        self._sync_emergency_cleanup()
        sys.exit(1)

    def _common_cleanup(self):
        """Common cleanup logic for both sync and async tests."""
        # Change back to original directory
        os.chdir(self.original_cwd)
        
        # Close database connection
        if hasattr(self, 'db_manager') and self.db_manager:
            self.db_manager.close()
        
        # Check config for cleanup settings from global config
        should_delete_db, should_delete_config = self._get_cleanup_settings()
        
        # Clean up test files based on configuration
        if should_delete_db and os.path.exists(self.db_file):
            os.remove(self.db_file)
            print(f"Cleaned up test database: {self.db_file}")
        
        if should_delete_config and os.path.exists(self.config_file):
            os.remove(self.config_file)
            print(f"Cleaned up test config: {self.config_file}")
    
    def _sync_emergency_cleanup(self):
        """Synchronous emergency cleanup - used by signal handlers and atexit."""
        try:
            self._common_cleanup()
        except Exception as e:
            print(f"Error during emergency cleanup: {e}")
    
    def get_playwright_headless_setting(self):
        """Get the headless setting for Playwright from config."""
        return self.config_manager.getboolean("Playwright", "headless", fallback=True)
    
    def _get_cleanup_settings(self):
        """Get cleanup settings from global config file instead of test config."""
        try:
            # Read from global config file
            global_config_path = os.path.join(os.path.dirname(self.test_dir), "config.ini")
            if os.path.exists(global_config_path):
                from modules.config_manager import ConfigManager
                global_config = ConfigManager(config_file=global_config_path)
                should_delete_db = global_config.getboolean("Tests", "delete_test_db", fallback=False)
                should_delete_config = global_config.getboolean("Tests", "delete_test_config", fallback=True)
                return should_delete_db, should_delete_config
            else:
                # Fallback to defaults if global config doesn't exist
                return False, True
        except Exception:
            # Fallback to defaults if there's any error reading global config
            return False, True


class BaseTest(BaseTestMixin, unittest.TestCase):
    """Base test class with common setup/teardown functionality and proper cleanup handling."""
    
    def setUp(self):
        """Common setup for all tests."""
        self._common_setup()


class BaseAsyncTest(BaseTestMixin, unittest.IsolatedAsyncioTestCase):
    """Base async test class with common setup/teardown functionality and proper cleanup handling."""
    
    async def asyncSetUp(self):
        """Common async setup for all tests."""
        self._common_setup()
    
    async def asyncTearDown(self):
        """Async teardown for async tests."""
        print(f"Async Cleanup settings: delete_db={self._get_cleanup_settings()[0]}, delete_config={self._get_cleanup_settings()[1]}")
        self._common_cleanup()