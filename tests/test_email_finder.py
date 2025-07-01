
import unittest
from modules.email_finder import EmailFinder

class TestEmailFinder(unittest.TestCase):
    def setUp(self):
        self.email_finder = EmailFinder()

    def test_find_email(self):
        self.assertEqual(self.email_finder.find_email("example.com"), "info@example.com")
        self.assertEqual(self.email_finder.find_email("sub.example.com"), "info@sub.example.com")
        self.assertEqual(self.email_finder.find_email(""), "N/A")
        self.assertEqual(self.email_finder.find_email(None), "N/A")

    def test_verify_email(self):
        self.assertTrue(self.email_finder.verify_email("test@example.com"))
        self.assertFalse(self.email_finder.verify_email("invalid-email"))
        self.assertFalse(self.email_finder.verify_email("test@.com"))
        self.assertFalse(self.email_finder.verify_email("test@example"))

if __name__ == "__main__":
    unittest.main()


