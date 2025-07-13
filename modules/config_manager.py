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

import configparser
import os

class ConfigManager:
    def __init__(self, config_file='config/config.ini'):
        self.config = configparser.ConfigParser()
        # Use current working directory for relative paths, or absolute path if provided
        if os.path.isabs(config_file):
            self.config_file = config_file
        else:
            self.config_file = os.path.join(os.getcwd(), config_file)
        self.config.read(self.config_file)

    def get(self, section, option, fallback=None):
        return self.config.get(section, option, fallback=fallback)

    def getboolean(self, section, option, fallback=None):
        return self.config.getboolean(section, option, fallback=fallback)

    def getint(self, section, option, fallback=None):
        return self.config.getint(section, option, fallback=fallback)

    def getfloat(self, section, option, fallback=None):
        return self.config.getfloat(section, option, fallback=fallback)


