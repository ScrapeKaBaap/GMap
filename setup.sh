#!/bin/bash
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

echo "🚀 GMap Setup Script"
echo "===================="
echo

# Ask about Python environment
read -p "Do you want to create a new Python virtual environment? (y/N): " create_env

if [[ $create_env =~ ^[Yy]$ ]]; then
    echo "📦 Creating new Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created in ./venv"
    echo "💡 To activate it, run: source venv/bin/activate"
    echo

    # Ask if user wants to activate it now
    read -p "Do you want to activate the virtual environment now? (y/N): " activate_env
    if [[ $activate_env =~ ^[Yy]$ ]]; then
        echo "🔄 Activating virtual environment..."
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "⚠️  Remember to activate the virtual environment before installing dependencies:"
        echo "   source venv/bin/activate"
    fi
    echo
else
    echo "📝 Using current Python environment"
    echo
fi

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🌐 Installing Playwright browsers..."
playwright install

echo
echo "✅ Setup completed successfully!"
echo "📖 Check config/config.example.ini for configuration options"


