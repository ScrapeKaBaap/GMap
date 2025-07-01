import unittest
import os
import sys

# Import module functions - ensure they are designed to be called externally
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.database_manager import DatabaseManager
from modules.config_manager import ConfigManager

# Import base test from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from base_test import BaseTest

class TestDatabaseManager(BaseTest):
    def test_insert_company(self):
        # Test inserting a new company
        inserted = self.db_manager.insert_company(
            name="Test Company 1",
            address="123 Test St",
            phone="123-456-7890",
            website="www.testcompany1.com",
            email="info@testcompany1.com",
            search_query="tech companies in Testland"
        )
        self.assertTrue(inserted)
        self.assertTrue(self.db_manager.company_exists("Test Company 1", "tech companies in Testland"))

        # Test inserting a duplicate company (should not raise error, but company_exists should still be true)
        inserted_duplicate = self.db_manager.insert_company(
            name="Test Company 1",
            address="123 Test St",
            phone="123-456-7890",
            website="www.testcompany1.com",
            email="info@testcompany1.com",
            search_query="tech companies in Testland"
        )
        self.assertTrue(inserted_duplicate) # It will return True even if it's a duplicate, as the insert operation itself is successful

    def test_company_exists(self):
        self.assertFalse(self.db_manager.company_exists("Non Existent Company", "some query"))
        
        self.db_manager.insert_company(
            name="Existing Company",
            address="456 Main St",
            phone="987-654-3210",
            website="www.existing.com",
            email="contact@existing.com",
            search_query="tech companies in Existsville"
        )
        self.assertTrue(self.db_manager.company_exists("Existing Company", "tech companies in Existsville"))

if __name__ == "__main__":
    unittest.main()


