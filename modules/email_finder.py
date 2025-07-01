import requests
from modules.logger_config import setup_logging
from modules.internet_utils import wait_for_internet, InternetRestoredException
import re

logger = setup_logging()

class EmailFinder:
    def __init__(self):
        pass

    def find_email(self, domain):
        logger.info(f"Attempting to find email for domain: {domain}")
        # This is a placeholder. A real implementation would use a service or a more complex logic.
        # For demonstration, we'll simulate a common pattern: info@domain.com
        if domain and "." in domain:
            # Strip www. prefix if present to avoid emails like info@www.example.com
            clean_domain = domain.lower()
            if clean_domain.startswith("www."):
                clean_domain = clean_domain[4:]
                logger.info(f"Stripped 'www.' from domain: {domain} -> {clean_domain}")
            
            potential_email = f"info@{clean_domain}"
            logger.info(f"Generated potential email: {potential_email}")
            return potential_email
        logger.warning(f"Could not generate potential email for domain: {domain}")
        return "N/A"

    def verify_email(self, email):
        logger.info(f"Attempting to verify email: {email}")
        
        # Check internet connection before proceeding
        wait_for_internet()
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                retry_count += 1
                logger.info(f"Verifying email {email} - Attempt {retry_count}/{max_retries}")
                
                # Check internet connection with raise on restore
                wait_for_internet(raise_on_restore=True)
                
                # A more robust regex for email validation
                # This regex checks for: 
                # 1. A valid local part (before @)
                # 2. An @ symbol
                # 3. A valid domain part (after @) with at least one dot and characters before and after the dot
                regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" # Added \. to ensure a dot exists in the domain
                if re.match(regex, email):
                    logger.info(f"Email {email} passed basic format check.")
                    return True
                else:
                    logger.warning(f"Email {email} failed basic format check.")
                    return False
                    
            except InternetRestoredException:
                logger.warning(f"Internet connection restored during email verification for {email}. Retrying (Attempt {retry_count}/{max_retries})...")
                if retry_count >= max_retries:
                    logger.error(f"Failed to verify email {email} after {max_retries} attempts due to repeated internet interruptions.")
                    return False
                continue
                
            except Exception as e:
                logger.error(f"Error verifying email {email} on attempt {retry_count}: {e}")
                if retry_count >= max_retries:
                    logger.error(f"Failed to verify email {email} after {max_retries} attempts.")
                    return False
                # Wait a bit before retrying
                import time
                time.sleep(1)
                continue


