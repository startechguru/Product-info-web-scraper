# Python Web Scraping Project

## 1. Project Overview

This project is a **Python web scraper** for extracting product information from three websites:

- Target
- Walmart
- Food City

The scraper collects product data and saves the results in **JSON** and **CSV** files.

### Extracted Product Data

- Product name
- Brand
- Size / Volume
- Price
- Description
- Ingredients
- Product image

The project also handles **website loading problems** and reports errors properly.

---

## 2. Project Structure
PYTHON WEB SCRAPING/
│
├── output/
│ ├── products.csv
│ └── products.json
│
├── scrapers/
│ ├── pycache/
│ ├── base_scraper.py
│ ├── foodcity_scraper.py
│ ├── target_scraper.py
│ └── walmart_scraper.py
│
├── utils/
│ ├── pycache/
│ ├── helpers.py
│ └── logger.py
│
├── main.py
└── README.md

---

## 3. File Description

### main.py

Main entry point of the project.

Responsibilities:

- Contains product URLs
- Selects the correct scraper based on the website
- Runs the scraping process
- Saves results into JSON and CSV

### scrapers/base_scraper.py

Base class for all scrapers.

Features:

- Opens browser with **Playwright**
- Creates page context
- Provides safe helper methods

Example helper methods:

```python
safe_text()
safe_attr()
These methods prevent crashes when page elements are missing.
scrapers/target_scraper.py
Scraper for the Target website.
Features:
•	Handles unavailable Target product pages
•	Extracts related sub-product links if needed
•	Removes duplicate products
•	Extracts product details
scrapers/walmart_scraper.py
Scraper for the Walmart website.
Features:
•	Extracts product data
•	Detects blocked pages
•	Detects timeouts
•	Detects redirects
•	Handles loading issues
scrapers/foodcity_scraper.py
Scraper for the Food City website.
Features:
•	Extracts product data
•	Detects website loading problems
•	Detects access issues
utils/helpers.py
Contains helper functions such as:
clean_text()
Used for cleaning and formatting extracted data.
output/
Stores final scraped files:
•	products.json
•	products.csv
________________________________________
4. Libraries Used
Playwright
Used for:
•	Browser automation
•	Handling dynamic page loading
•	Interacting with JavaScript-based websites
re
Used for:
•	Regular expressions
•	Text matching
•	Data extraction
json
Used to:
•	Save output data in JSON format
csv
Used to:
•	Save output data in CSV format
os
Used for:
•	File handling
•	Folder creation
•	Path management
________________________________________
5. How the Problem Was Solved
Some websites load product information dynamically, so traditional scraping methods using requests + BeautifulSoup are not sufficient.
Solution
•	Use Playwright to open real browser pages
•	Wait for page content to fully load
•	Extract product information using CSS selectors
•	Use safe helper methods to avoid crashes when elements are missing
•	Handle unavailable pages
•	Retry by collecting valid sub-product links
•	Remove duplicate product results
•	Save results in structured output files
________________________________________
6. How Website Issues Are Detected
If a website does not load properly or has issues, the scraper detects it in several ways.
Timeout Detection
If page loading takes too long, Playwright throws a timeout error.
Exception Detection
If browser or page actions fail:
•	Exceptions are caught
•	Errors are logged
Content-Based Detection
The scraper checks page text for messages such as:
•	page not found
•	item not available
•	access denied
•	service unavailable
•	verify your identity
Invalid Page or Redirect Detection
If the final loaded URL is unexpected, the scraper reports it as an error.
Missing Required Product Data
If important data like product title is missing:
•	The scraper marks the result as failed.
________________________________________
7. How Website Issues Are Handled
The scraper handles website problems safely using:
•	try / except blocks
•	Timeout detection
•	Page loading error detection
•	Structured error responses
Instead of crashing, the scraper returns a failed result object.
Example Failed Result
{
  "website": "Walmart",
  "url": "...",
  "product_name": "",
  "brand": "",
  "size": "",
  "price": "",
  "description": "",
  "ingredients": "",
  "image_url": "",
  "status": "failed",
  "error": "Page load timeout"
}
This makes the scraper:
•	Stable
•	Easier to debug
•	Reliable for batch scraping
________________________________________
8. How to Run the Project
Step 1 — Install Python
Install Python 3.9 or higher.
Step 2 — Install Required Package
pip install playwright
Step 3 — Install Browser for Playwright
playwright install
Step 4 — Run the Project
python main.py
________________________________________
9. Output
After running the scraper, the output files will be created in the output/ folder.
Generated Files
•	output/products.json
•	output/products.csv
JSON File
•	Data grouped by website
CSV File
•	All scraped products in tabular format
________________________________________
10. Notes
•	Some websites may block scraping
•	Some pages may load slowly
•	Some product pages may not contain all fields
In these cases:
•	The scraper reports the issue in the "error" field.
The Target scraper may collect product data from related sub-pages if the main page is unavailable.
________________________________________
11. Summary
This project is a multi-site product scraper built with Python and Playwright.
Features
•	Scrapes product data from Target, Walmart, and Food City
•	Handles dynamic websites
•	Detects loading issues
•	Safely handles errors
•	Removes duplicate products
•	Saves clean JSON and CSV outputs
The project is designed to be robust, scalable, and easy to debug.

