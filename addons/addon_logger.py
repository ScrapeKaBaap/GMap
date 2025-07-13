#!/usr/bin/env python3
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

"""
Addon Logger Configuration

Enhanced logger that can be used by addons with their own log directories.
Uses the same logger_config.py from geo_mail but allows custom log directories.
"""

import logging
import os
import sys
import shutil
from datetime import datetime
from typing import Optional

def setup_addon_logging(addon_name: str, custom_log_dir: Optional[str] = None):
    """
    Set up logging for an addon with its own log directory.
    
    Args:
        addon_name: Name of the addon (e.g., 'mail-harvester', 'static-generator')
        custom_log_dir: Custom log directory path (optional)
        
    Returns:
        Logger instance
    """
    
    # Determine log directory
    if custom_log_dir:
        log_dir = custom_log_dir
    else:
        # Default: addon's own logs directory
        addon_dir = os.path.dirname(os.path.abspath(__file__))
        if addon_name in addon_dir:
            # We're in the addon directory
            log_dir = os.path.join(addon_dir, "logs")
        else:
            # We're being called from elsewhere, construct path
            geo_mail_root = os.path.dirname(addon_dir)
            log_dir = os.path.join(geo_mail_root, "addons", addon_name, "logs")
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Generate timestamped run folder
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_folder = os.path.join(log_dir, timestamp)
    os.makedirs(run_folder, exist_ok=True)
    
    # Default logging configuration (can be overridden by config)
    console_level = "INFO"
    file_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    max_log_files = 10
    
    # Try to load configuration from geo_mail config if available
    try:
        # Add geo_mail modules to path
        geo_mail_modules = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules")
        if geo_mail_modules not in sys.path:
            sys.path.insert(0, geo_mail_modules)
        
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        
        console_level = config_manager.get("Logging", "console_level", fallback="INFO").upper()
        file_levels = [level.strip().upper() for level in config_manager.get("Logging", "file_levels", fallback="DEBUG,INFO,WARNING,ERROR,CRITICAL").split(",")]
        max_log_files = config_manager.getint("Logging", "max_log_files_to_keep", fallback=10)
        
    except Exception as e:
        print(f"Warning: Could not load geo_mail config, using defaults: {e}")
    
    # Clear any existing handlers for this logger
    logger_name = f"addon.{addon_name}"
    addon_logger = logging.getLogger(logger_name)
    
    # Clear existing handlers
    for handler in addon_logger.handlers[:]:
        addon_logger.removeHandler(handler)
    
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
            file_handler.setFormatter(logging.Formatter(
                f"%(asctime)s - %(levelname)s - {addon_name} - %(module)s - %(message)s"
            ))
            
            # Add filter to only show this level
            file_handler.addFilter(lambda record, lvl=level: record.levelname == lvl)
            file_handlers.append(file_handler)
    
    # Create console handler with configured level
    console_handler = logging.StreamHandler()
    try:
        console_handler.setLevel(getattr(logging, console_level))
    except AttributeError:
        console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        f"%(asctime)s - %(levelname)s - {addon_name} - %(message)s"
    ))
    
    # Create "all" log file that contains everything
    all_log_file = os.path.join(run_folder, "all.log")
    log_files["ALL"] = all_log_file
    all_handler = logging.FileHandler(all_log_file)
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(logging.Formatter(
        f"%(asctime)s - %(levelname)s - {addon_name} - %(module)s - %(message)s"
    ))
    
    # Configure addon logger
    addon_logger.setLevel(logging.DEBUG)
    addon_logger.propagate = False  # Don't propagate to root logger
    
    for handler in file_handlers:
        addon_logger.addHandler(handler)
    addon_logger.addHandler(all_handler)
    addon_logger.addHandler(console_handler)
    
    # Write CLI command and configuration to all log files
    cli_command = " ".join(sys.argv)
    config_info = f"Console Level: {console_level}, File Levels: {file_levels}"
    header = f"Addon: {addon_name}\nCLI Command: {cli_command}\nLogging Config: {config_info}\n{'=' * 80}\n\n"
    
    for log_file in log_files.values():
        with open(log_file, "w") as f:
            f.write(header)
    
    addon_logger.info(f"Addon logging initialized for {addon_name}")
    addon_logger.info(f"Log directory: {run_folder}")
    addon_logger.info(f"CLI Command: {cli_command}")
    addon_logger.info(f"Console showing: {console_level} level logs")
    addon_logger.info(f"File levels: {', '.join(file_levels)}")
    
    # Clean up old log folders
    _cleanup_old_logs(log_dir, max_log_files, addon_logger)
    
    return addon_logger

def _cleanup_old_logs(log_dir, max_files_to_keep, logger):
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
                    logger.debug(f"Removed old log folder: {folder_path}")
                except Exception as e:
                    logger.warning(f"Could not remove old log folder {folder_path}: {e}")
    
    except Exception as e:
        logger.warning(f"Error during log cleanup: {e}")

def _is_valid_log_folder(folder_name):
    """Check if folder name matches the expected timestamped format: YYYY-MM-DD_HHMMSS."""
    try:
        # Try to parse the folder name as a timestamp
        datetime.strptime(folder_name, "%Y-%m-%d_%H%M%S")
        return True
    except ValueError:
        return False

def get_addon_logger(addon_name: str):
    """
    Get an existing addon logger or create a new one.
    
    Args:
        addon_name: Name of the addon
        
    Returns:
        Logger instance
    """
    logger_name = f"addon.{addon_name}"
    logger = logging.getLogger(logger_name)
    
    # If logger doesn't have handlers, set it up
    if not logger.handlers:
        logger = setup_addon_logging(addon_name)
    
    return logger
