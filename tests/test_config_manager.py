import unittest
import os
import sys

# Import module functions - ensure they are designed to be called externally
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.config_manager import ConfigManager

# Import base test from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from base_test import BaseTest

class TestConfigManager(BaseTest):
    pass

    def test_get(self):
        self.assertEqual(self.config_manager.get("TestSection", "key1"), "value1")
        self.assertIsNone(self.config_manager.get("TestSection", "non_existent_key"))
        self.assertEqual(self.config_manager.get("TestSection", "non_existent_key", fallback="default"), "default")

    def test_getint(self):
        self.assertEqual(self.config_manager.getint("TestSection", "key2"), 123)

    def test_getboolean(self):
        self.assertTrue(self.config_manager.getboolean("TestSection", "key3"))

if __name__ == "__main__":
    unittest.main()


