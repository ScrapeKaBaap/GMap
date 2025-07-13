
# ================================================================================
# GMap - Professional Google Maps Scraper & Email Discovery Platform
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: GMap - Automated Google Maps Scraping + Email Discovery System
# Repository: https://github.com/ScrapeKaBaap/GMap
#
# Description: Enterprise-grade business intelligence platform that combines
#              automated Google Maps scraping with advanced email discovery
#              techniques to build targeted business contact databases.
#
# Components: - Google Maps Company Scraper
#             - Multi-Method Email Discovery (Static, Harvester, Scraper, Checker)
#             - Professional Database Management
#             - Advanced Configuration & Logging System
#
# License: MIT License
# Created: 2025
#
# ================================================================================
# This file is part of the GMap project.
# For complete documentation, visit: https://github.com/ScrapeKaBaap/GMap
# ================================================================================

import logging
import os
import shutil
import sys
from datetime import datetime
from modules.config_manager import ConfigManager

# Get the base directory (project root - parent of modules directory)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Sets up multi-level logging configuration with separate files per log level in timestamped folders."""
    config_manager = ConfigManager()
    
    log_dir = config_manager.get("Logging", "log_dir", fallback="logs")
    # If it's a relative path, make it relative to BASE_DIR
    if not os.path.isabs(log_dir):
        log_dir = os.path.join(BASE_DIR, log_dir)
    
    # Create main logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Generate timestamped run folder with cleaner naming: YYYY-MM-DD_HHMMSS
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_folder = os.path.join(log_dir, timestamp)
    os.makedirs(run_folder, exist_ok=True)
    
    # Get logging configuration
    console_level = config_manager.get("Logging", "console_level", fallback="INFO").upper()
    file_levels = [level.strip().upper() for level in config_manager.get("Logging", "file_levels", fallback="DEBUG,INFO,WARNING,ERROR,CRITICAL").split(",")]
    max_log_files = config_manager.getint("Logging", "max_log_files_to_keep", fallback=10)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set up file handlers for each log level
    file_handlers = []
    log_files = {}
    
    for level in file_levels:
        if level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            log_file = os.path.join(run_folder, f"{level.lower()}.log")
            log_files[level] = log_file
            
            # Create file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level))
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s"))
            
            # Add filter to only show this level
            file_handler.addFilter(lambda record, lvl=level: record.levelname == lvl)
            file_handlers.append(file_handler)
    
    # Create console handler with configured level
    console_handler = logging.StreamHandler()
    try:
        console_handler.setLevel(getattr(logging, console_level))
    except AttributeError:
        console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s"))
    
    # Create "all" log file that contains everything
    all_log_file = os.path.join(run_folder, "all.log")
    log_files["ALL"] = all_log_file
    all_handler = logging.FileHandler(all_log_file)
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s"))
    
    # Configure root logger
    root_logger.setLevel(logging.DEBUG)
    for handler in file_handlers:
        root_logger.addHandler(handler)
    root_logger.addHandler(all_handler)
    root_logger.addHandler(console_handler)
    
    logger = logging.getLogger(__name__)
    
    # Write CLI command and configuration to all log files
    cli_command = " ".join(sys.argv)
    config_info = f"Console Level: {console_level}, File Levels: {file_levels}"
    header = f"CLI Command: {cli_command}\nLogging Config: {config_info}\n{'=' * 80}\n\n"
    
    for log_file in log_files.values():
        with open(log_file, "w") as f:
            f.write(header)
    
    logger.info(f"Multi-level logging initialized in: {run_folder}")
    logger.info(f"CLI Command: {cli_command}")
    logger.info(f"Console showing: {console_level} level logs")
    logger.info(f"File levels: {', '.join(file_levels)}")
    
    # Clean up old log folders
    _cleanup_old_logs(log_dir, max_log_files)
    
    return logger

def _cleanup_old_logs(log_dir, max_files_to_keep):
    """Clean up old log folders, keeping only the most recent ones."""
    try:
        if not os.path.exists(log_dir):
            return
        
        # Get all timestamped folders (YYYY-MM-DD_HHMMSS format)
        log_folders = []
        for item in os.listdir(log_dir):
            item_path = os.path.join(log_dir, item)
            if os.path.isdir(item_path) and _is_valid_log_folder(item):
                log_folders.append((item_path, os.path.getctime(item_path)))
        
        # Sort by creation time (newest first)
        log_folders.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old folders if we exceed the limit
        if len(log_folders) > max_files_to_keep:
            folders_to_remove = log_folders[max_files_to_keep:]
            for folder_path, _ in folders_to_remove:
                try:
                    shutil.rmtree(folder_path)
                    logging.debug(f"Removed old log folder: {folder_path}")
                except Exception as e:
                    logging.warning(f"Could not remove old log folder {folder_path}: {e}")
    
    except Exception as e:
        logging.warning(f"Error during log cleanup: {e}")

def _is_valid_log_folder(folder_name):
    """Check if folder name matches the expected timestamped format: YYYY-MM-DD_HHMMSS."""
    try:
        # Try to parse the folder name as a timestamp
        datetime.strptime(folder_name, "%Y-%m-%d_%H%M%S")
        return True
    except ValueError:
        return False

# Initialize logger (can be imported by other modules)
logger = setup_logging()


