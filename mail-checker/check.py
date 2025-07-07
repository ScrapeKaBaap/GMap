import sqlite3
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os
import time

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.logger_config import logger
from modules.config_manager import ConfigManager

# --- Configuration Variables ---
# These will be loaded from config.ini
DB_NAME = None
TABLE_NAME = None
EMAIL_COLUMN_NAME = None
LOCAL_API_ENDPOINT = None
DB_FETCH_BATCH_SIZE = None
MAX_WORKERS = None
MAX_API_REQUESTS_TOTAL = None
API_TIMEOUT = 3600 # seconds

def load_config():
    """Load configuration from config.ini file."""
    global DB_NAME, TABLE_NAME, EMAIL_COLUMN_NAME, LOCAL_API_ENDPOINT
    global DB_FETCH_BATCH_SIZE, MAX_WORKERS, MAX_API_REQUESTS_TOTAL
    
    config = ConfigManager()
    
    # Load database configuration
    DB_NAME = config.get("Database", "db_name", fallback="Maps_companies.db")
    
    # Load email configuration
    TABLE_NAME = config.get("Email", "table_name", fallback="companies")
    EMAIL_COLUMN_NAME = config.get("Email", "email_column", fallback="email")
    LOCAL_API_ENDPOINT = config.get("Email", "api_endpoint", fallback="http://localhost:8080/v0/check_email")
    DB_FETCH_BATCH_SIZE = config.getint("Email", "batch_size", fallback=200)
    MAX_WORKERS = config.getint("Email", "max_workers", fallback=10)
    
    # Handle empty max_requests_total (means no limit)
    max_requests_str = config.get("Email", "max_requests_total", fallback="")
    MAX_API_REQUESTS_TOTAL = int(max_requests_str) if max_requests_str else None
    
    logger.info(f"Configuration loaded - DB: {DB_NAME}, Table: {TABLE_NAME}, Email Column: {EMAIL_COLUMN_NAME}")

# --- Logging Setup ---
# Using custom logger from logger_config.py

def setup_database(db_name=None, table_name=None):
    """
    Connects to the SQLite database and adds new columns if they don't exist.
    """
    if db_name is None:
        db_name = DB_NAME
    if table_name is None:
        table_name = TABLE_NAME
        
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Core new columns for the request
        columns_to_add = {
            'is_reachable': 'TEXT',
            'mx_accepts_mail': 'BOOLEAN',
            'records': 'TEXT', # Storing JSON string of the list
            'is_disposable': 'BOOLEAN',
            'is_role_account': 'BOOLEAN',
            'is_valid_syntax': 'BOOLEAN',
            'can_connect_smtp': 'BOOLEAN',
            'is_deliverable': 'BOOLEAN',
            'is_catch_all': 'BOOLEAN',
            'has_full_inbox': 'BOOLEAN',
            'is_disabled': 'BOOLEAN'
            # 'domain' and 'username' are explicitly excluded as per request
        }

        for col_name, col_type in columns_to_add.items():
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                logger.info(f"DB Setup: Added '{col_name}' column to '{table_name}'.")
            except sqlite3.OperationalError as e:
                if f"duplicate column name: {col_name}" not in str(e):
                    logger.error(f"DB Setup: Error adding {col_name} column: {e}")
                else:
                    logger.info(f"DB Setup: '{col_name}' column already exists in '{table_name}'.")

        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"DB Setup: Database error during setup: {e}")
    finally:
        if conn:
            conn.close()

def check_email_api(email, email_id, api_endpoint=None): # Added email_id here
    """
    Sends a request to the local email checking endpoint.
    Returns the parsed JSON response or None on error.
    """
    if api_endpoint is None:
        api_endpoint = LOCAL_API_ENDPOINT
        
    headers = {"Content-Type": "application/json"}
    data = {"to_email": email}
    try:
        # Log before sending request
        logger.debug(f"API Call: Sending request for ID {email_id}, Email: {email}")
        response = requests.post(api_endpoint, headers=headers, json=data, timeout=API_TIMEOUT)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        json_response = response.json()
        logger.debug(f"API Call: Success for ID {email_id}, Email: {email}. Status: {response.status_code}")
        return json_response
    except requests.exceptions.Timeout:
        logger.warning(f"API Call: Timeout occurred for ID {email_id}, Email: {email}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"API Call: HTTP Error {e.response.status_code} for ID {email_id}, Email: {email}: {e.response.text}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"API Call: Connection Error for ID {email_id}, Email: {email}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"API Call: Generic Request Exception for ID {email_id}, Email: {email}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.warning(f"API Call: JSON Decode Error for ID {email_id}, Email: {email}: {e}. Response: {response.text[:200]}...")
        return None


def process_email_data(email_id, email_address, api_response):
    """
    Extracts relevant data from the API response and prepares it for DB update.
    Returns a dictionary of column_name: value pairs.
    """
    if not api_response:
        logger.debug(f"Processing: No API response provided for ID {email_id}, Email: {email_address}.")
        return None

    update_data = {
        'id': email_id,
        'is_reachable': api_response.get('is_reachable'),
        'mx_accepts_mail': api_response.get('mx', {}).get('accepts_mail'),
        'records': json.dumps(api_response.get('mx', {}).get('records', []))
    }

    # Optional: Add more data from the API response (excluding domain and username)
    misc = api_response.get('misc', {})
    update_data['is_disposable'] = misc.get('is_disposable')
    update_data['is_role_account'] = misc.get('is_role_account')

    syntax = api_response.get('syntax', {})
    update_data['is_valid_syntax'] = syntax.get('is_valid_syntax')

    smtp = api_response.get('smtp', {})
    update_data['can_connect_smtp'] = smtp.get('can_connect_smtp')
    update_data['is_deliverable'] = smtp.get('is_deliverable')
    update_data['is_catch_all'] = smtp.get('is_catch_all')
    update_data['has_full_inbox'] = smtp.get('has_full_inbox')
    update_data['is_disabled'] = smtp.get('is_disabled')

    logger.debug(f"Processing: Data prepared for ID {email_id}, Email: {email_address}. Is_reachable: {update_data['is_reachable']}")
    return update_data

def update_database_record(conn, cursor, data, table_name=None):
    """
    Updates a single record in the database with the processed email data.
    """
    if not data:
        logger.warning("DB Update: No data provided for database update.")
        return False
        
    if table_name is None:
        table_name = TABLE_NAME

    record_id = data['id']
    try:
        # Construct the SET part of the UPDATE statement dynamically
        set_clauses = []
        values = []
        for key, value in data.items():
            if key != 'id': # 'id' is used in WHERE clause
                set_clauses.append(f"{key} = ?")
                values.append(value)
        values.append(record_id) # Add id for the WHERE clause

        update_sql = f"""
            UPDATE {table_name}
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """
        cursor.execute(update_sql, values)
        logger.debug(f"DB Update: Successfully prepared update for ID {record_id}.")
        return True
    except sqlite3.Error as e:
        logger.error(f"DB Update: Error preparing update for ID {record_id}: {e}")
        return False

# Re-added check_single_email and update_email_in_database for modularity as you had them
# and they might be called from other modules. Their logging remains concise.
def check_single_email(email, email_id=None, db_name=None, table_name=None, api_endpoint=None):
    """
    Check a single email and return the processed data.
    This function is independent and can be called from other modules.
    """
    if db_name is None:
        db_name = DB_NAME
    if table_name is None:
        table_name = TABLE_NAME
    if api_endpoint is None:
        api_endpoint = LOCAL_API_ENDPOINT
        
    if DB_NAME is None: # Check if configuration is loaded for standalone calls
        load_config()
    
    setup_database(db_name, table_name) # Ensure columns exist
    
    api_response = check_email_api(email, email_id, api_endpoint) # Pass email_id
    
    if api_response:
        processed_data = process_email_data(email_id, email, api_response)
        return processed_data
    else:
        logger.warning(f"Single Check: No API response for email ID {email_id}, Email: {email}")
        return None

def update_email_in_database(email, email_id, processed_data, db_name=None, table_name=None):
    """
    Update a single email's data in the database.
    This function is independent and can be called from other modules.
    """
    if db_name is None:
        db_name = DB_NAME
    if table_name is None:
        table_name = TABLE_NAME
        
    if not processed_data:
        return False
        
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        if 'id' not in processed_data:
            processed_data['id'] = email_id
            
        success = update_database_record(conn, cursor, processed_data, table_name)
        if success:
            conn.commit()
            logger.info(f"Single Update: Successfully committed update for email ID {email_id}, Email: {email}.")
            return True
        else:
            logger.error(f"Single Update: Failed to update record for email ID {email_id}, Email: {email}. (update_database_record returned False)")
            return False
    except sqlite3.Error as e:
        logger.error(f"Single Update: Database error committing update for email ID {email_id}, Email: {email}: {e}")
        return False
    finally:
        if conn:
            conn.close()

def check_and_update_email(email, email_id, db_name=None, table_name=None, api_endpoint=None):
    """
    Complete function to check an email and update the database.
    This is the main function that other modules should call.
    """
    if DB_NAME is None:
        load_config()
        
    processed_data = check_single_email(email, email_id, db_name, table_name, api_endpoint)
    
    if processed_data:
        success = update_email_in_database(email, email_id, processed_data, db_name, table_name)
        return success
    else:
        logger.warning(f"Check & Update: Failed to get processed data for email ID {email_id}, Email: {email}. Skipping DB update.")
        return False


def main():
    # Load configuration from config.ini
    load_config()
    
    setup_database()

    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        current_offset = 0 
        total_api_requests_made = 0 

        while True:
            if MAX_API_REQUESTS_TOTAL is not None and total_api_requests_made >= MAX_API_REQUESTS_TOTAL:
                logger.info(f"Main Loop: Reached MAX_API_REQUESTS_TOTAL ({MAX_API_REQUESTS_TOTAL}). Stopping.")
                break

            select_sql = f"""
                SELECT id, {EMAIL_COLUMN_NAME} FROM {TABLE_NAME}
                WHERE is_reachable IS NULL OR mx_accepts_mail IS NULL OR records IS NULL
                ORDER BY id ASC
                LIMIT ? OFFSET ?
            """
            cursor.execute(select_sql, (DB_FETCH_BATCH_SIZE, current_offset))
            emails_to_process = cursor.fetchall()

            if not emails_to_process:
                logger.info("Main Loop: No more emails to process or all relevant emails have been processed.")
                break

            fetched_ids = [email[0] for email in emails_to_process]
            min_id = min(fetched_ids) if fetched_ids else 'N/A'
            max_id = max(fetched_ids) if fetched_ids else 'N/A'

            logger.info(f"Main Loop: Fetched {len(emails_to_process)} emails (IDs from {min_id} to {max_id}) starting from internal offset {current_offset}.")

            # Use ThreadPoolExecutor for concurrent API requests
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Pass email_id to check_email_api for better internal logging
                future_to_email = {executor.submit(check_email_api, email_data[1], email_data[0]): email_data
                                   for email_data in emails_to_process}
                
                batch_updates = []
                successfully_updated_ids = [] # To log actual updated IDs after commit
                failed_api_check_ids = [] # To log IDs that failed API check
                
                for future in as_completed(future_to_email):
                    if MAX_API_REQUESTS_TOTAL is not None and total_api_requests_made >= MAX_API_REQUESTS_TOTAL:
                        logger.info(f"Main Loop: Stopping current batch due to MAX_API_REQUESTS_TOTAL limit.")
                        break

                    email_id, email_address = future_to_email[future] # Re-fetch original tuple
                    
                    try:
                        api_response = future.result() # This is the result from check_email_api
                        
                        if api_response:
                            processed_data = process_email_data(email_id, email_address, api_response)
                            if processed_data:
                                batch_updates.append(processed_data)
                                total_api_requests_made += 1
                                # Individual success logging is now handled within update_database_record if debug is on,
                                # and a summary for the batch will be logged.
                            else:
                                # This case means API call was OK, but process_email_data failed (unlikely if API response is valid JSON)
                                logger.warning(f"Batch Process: Could not process API response for ID {email_id}, Email: {email_address}. Skipping DB update.")
                                failed_api_check_ids.append(email_id)
                        else:
                            # This case means check_email_api returned None (API call itself failed/timed out/bad response)
                            logger.warning(f"Batch Process: API check failed for ID {email_id}, Email: {email_address}. No data to update.")
                            failed_api_check_ids.append(email_id)

                    except Exception as exc:
                        logger.error(f"Batch Process: Unhandled exception for ID {email_id}, Email: {email_address}: {exc}")
                        failed_api_check_ids.append(email_id)

            # Apply batch updates to the database
            if batch_updates:
                conn.execute("BEGIN TRANSACTION;") # Start transaction for batch update
                try:
                    for data in batch_updates:
                        if update_database_record(conn, cursor, data): # Call update_database_record
                            successfully_updated_ids.append(data['id'])
                        else:
                            # If update_database_record returns False, it means there was an error in preparing it
                            logger.error(f"Batch Commit: Failed to prepare database update for ID {data['id']}. Skipping this record from batch commit.")
                            if data['id'] in successfully_updated_ids: # Remove if it was somehow added
                                successfully_updated_ids.remove(data['id'])
                            # Don't add to failed_api_check_ids as API check might have been fine
                            # but DB update failed.
                            
                    conn.commit()
                    logger.info(f"Batch Commit: Successfully committed {len(successfully_updated_ids)} updates. Updated IDs: {successfully_updated_ids}")
                except sqlite3.Error as e:
                    conn.rollback() # Rollback on any error during batch commit
                    logger.critical(f"Batch Commit: Database error during batch commit. Rolled back transaction: {e}")
                    # Log IDs that were *intended* to be updated but might not have been due to rollback
                    logger.warning(f"Batch Commit: IDs that were part of the failed commit attempt: {[d['id'] for d in batch_updates]}")
            else:
                logger.info("Batch Commit: No successful API responses in this batch to commit.")
                
            if failed_api_check_ids:
                logger.warning(f"Batch Summary: Emails that failed API check or processing in this batch (IDs): {failed_api_check_ids}")

            current_offset += len(emails_to_process) 
            
            if len(emails_to_process) < DB_FETCH_BATCH_SIZE:
                logger.info(f"Main Loop: Less than {DB_FETCH_BATCH_SIZE} emails fetched, assuming end of undone records for current offset.")
                # This could be a true end, or just a sparse section.
                # To be absolutely sure you are done, you might re-query with offset 0
                # or just let the next iteration confirm no new emails.
                # For robustness, we'll let it loop once more to confirm
                # that `emails_to_process` is empty.
                
            time.sleep(0.1)

    except sqlite3.Error as e:
        logger.error(f"Main Loop: Database error during main processing: {e}")
    except Exception as e:
        logger.critical(f"Main Loop: An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Main Loop: Database connection closed.")

if __name__ == "__main__":
    main()