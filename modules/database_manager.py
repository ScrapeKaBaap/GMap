import sqlite3
import os
from modules.config_manager import ConfigManager

class DatabaseManager:
    def __init__(self, config_manager=None):
        if config_manager is None:
            config_manager = ConfigManager()
        
        db_name = config_manager.get("Database", "db_name", fallback="google_maps_companies.db")
        # Use current working directory for relative paths, or join with current dir if not absolute
        if os.path.isabs(db_name):
            self.db_path = db_name
        else:
            self.db_path = os.path.join(os.getcwd(), db_name)
        
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_table()

    def _connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def _create_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    phone TEXT,
                    website TEXT,
                    email TEXT,
                    search_query TEXT
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def insert_company(self, name, address, phone, website, email, search_query):
        try:
            self.cursor.execute("""
                INSERT INTO companies (name, address, phone, website, email, search_query)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, address, phone, website, email, search_query))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error inserting company: {e}")
            return False

    def get_last_inserted_company_id(self):
        """Get the ID of the last inserted company."""
        try:
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error getting last inserted company ID: {e}")
            return None

    def company_exists(self, name, search_query):
        self.cursor.execute("SELECT 1 FROM companies WHERE name = ? AND search_query = ?", (name, search_query))
        return self.cursor.fetchone() is not None

    def close(self):
        if self.conn:
            self.conn.close()

    def __del__(self):
        self.close()


