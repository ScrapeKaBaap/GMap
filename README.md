
# Google Maps Scraper

This project provides a comprehensive and modular solution for scraping company information from Google Maps using Playwright.

## Features

- **Configurable Search Queries**: Define search query templates and parameters in `config.ini`.
- **Playwright Automation**: Utilizes Playwright for robust web scraping.
- **SQLite Database**: Stores scraped company data in a SQLite database.
- **Modular Design**: Code is organized into modules for reusability and maintainability.
- **Comprehensive Logging**: Multi-level logging with timestamped folders for detailed tracking.
- **Domain-to-Email Functionality**: Attempts to find company emails based on their website domains.
- **Test Modules**: Includes unit tests for core functionalities.

## Project Structure

```
google_maps_scraper/
├── config.ini
├── setup.sh
├── requirements.txt
├── README.md
├── src/
│   └── main.py
├── modules/
│   ├── __init__.py
│   ├── config_manager.py
│   ├── database_manager.py
│   ├── email_finder.py
│   └── google_maps_scraper.py
├── tests/
│   ├── test_config_manager.py
│   ├── test_database_manager.py
│   ├── test_email_finder.py
│   └── test_google_maps_scraper.py
└── logs/
```

## Setup

1.  **Clone the repository (if applicable):**

    ```bash
    git clone <repository_url>
    cd google_maps_scraper
    ```

2.  **Run the setup script:**

    This script will install all necessary Python dependencies and Playwright browsers.

    ```bash
    bash setup.sh
    ```

## Configuration

Edit the `config.ini` file to customize the scraper behavior:

```ini
[Search]
search_query_templates = tech companies in ${country}, tech companies in ${state}
country = Australia, Austria, Belgium
state = Amsterdam, Antwerp, Barcelona
scroll_count = 5

[Database]
db_name = google_maps_companies.db

[Logging]
console_level = INFO
file_levels = DEBUG,INFO,WARNING,ERROR,CRITICAL
max_log_files_to_keep = 10
log_dir = logs

[Playwright]
headless = True
```

-   `search_query_templates`: Define templates for your search queries. Use `${variable_name}` for dynamic substitution.
-   `country`, `state`: Provide comma-separated values for the variables used in `search_query_templates`.
-   `scroll_count`: Number of times to scroll down the search results page to load more companies.
-   `db_name`: Name of the SQLite database file.
-   `console_level`: Logging level for console output (DEBUG, INFO, WARNING, ERROR, CRITICAL).
-   `file_levels`: Comma-separated logging levels for separate log files.
-   `max_log_files_to_keep`: Maximum number of old log folders to retain.
-   `log_dir`: Directory for storing log files.
-   `headless`: Set to `True` to run Playwright in headless mode (without a visible browser UI), `False` otherwise.

## Usage

To run the scraper, execute the `main.py` script:

```bash
python3.11 src/main.py
```

The scraper will generate search queries based on your `config.ini`, scrape data from Google Maps, and store it in the specified SQLite database.

## Testing

To run the unit tests, execute the following command from the project root directory:

```bash
PYTHONPATH=. python3.11 -m unittest discover tests
```

## Troubleshooting

If you encounter issues with Playwright, ensure all its dependencies are correctly installed. Refer to the Playwright documentation for more details.

If the scraper is not working as expected, manually open `maps.google.com` in your VM's browser and perform the search to understand the current page structure and identify any changes that might affect the scraping logic.


