import socket
import time
import random
from modules.logger_config import logger

# Custom exception for signaling that the internet connection was lost and restored
class InternetRestoredException(Exception):
    """Exception raised when the internet connection was lost and then restored."""
    pass

def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """
    Check for internet connectivity by attempting to connect to a known host.
    Host: 8.8.8.8 (Google Public DNS)
    Port: 53/tcp
    Timeout: 3 seconds
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        # Log only if it's a network unreachable error, otherwise debug
        # Common errors: [Errno 101] Network is unreachable, [Errno 111] Connection refused, [Errno 113] No route to host
        if isinstance(ex, socket.gaierror) or (hasattr(ex, 'errno') and ex.errno in [101, 111, 113]):
             logger.warning(f"Internet connection check failed: {ex}")
        else:
             logger.debug(f"Internet connection check failed (other): {ex}")
        return False

def wait_for_internet(check_interval=60, raise_on_restore=False):
    """
    Continuously checks for internet connection and waits if unavailable.
    Pauses execution until the internet connection is restored.
    Includes delays to mimic human behavior for anti-detection.

    Args:
        check_interval (int): Seconds between connection checks when offline.
        raise_on_restore (bool): If True, raises InternetRestoredException when connection is restored after being lost.
                                 If False (default), simply logs restoration and returns.
    """
    connection_was_lost = False
    while not check_internet_connection():
        if not connection_was_lost:
            logger.info(f"Internet connection lost. Waiting for {check_interval} seconds before retrying...")
            connection_was_lost = True
        time.sleep(check_interval)
        # Add a small random delay after waiting to mimic human behavior
        random_delay = random.uniform(1, 5)
        logger.debug(f"Adding random delay of {random_delay:.2f} seconds.")
        time.sleep(random_delay)
        
    if connection_was_lost:
        logger.info("Internet connection restored. Resuming operation.")
        if raise_on_restore:
            raise InternetRestoredException("Internet connection was restored after an interruption.")


