# Review Scraper (Assignment)

## Objective
Python script to scrape software product reviews from multiple sources (G2 and Capterra), filter them by date range, and export a clean JSON file that can be used for analysis.

## How it works
- User runs:  
  `python code.py "<company_name>" <start_date> <end_date> <source>`
- Script:
  - Reads CLI inputs (company, start date, end date, source).
  - Builds the review URL for the selected source.
  - Fetches all review pages (pagination) using `requests`.
  - Parses each page with `BeautifulSoup` to extract:
    - title, date, rating, reviewer name, review text.
  - Keeps only reviews within the given date range.
  - Saves all reviews into `<company>_<source)_reviews.json`.

## Input & Output
- **Input (CLI):**
  - `company_name` – e.g. `"HubSpot"`.
  - `start_date`, `end_date` – `YYYY-MM-DD`.
  - `source` – `g2` or `capterra`.
- **Output (file):**
  - JSON array; each object has:
    - `title`, `date`, `rating`, `reviewer_name`, `review_text`, `source`, `company`.

## Tech stack
- Language: Python 3  
- Libraries: `requests`, `beautifulsoup4`, `dataclasses`, `json`, `datetime`.

Install dependencies:
pip install requests beautifulsoup4


## Notes / Limitations
- Many real review sites load data via JavaScript or use bot protection, so `requests` may see very little HTML and the script can return an empty list of reviews.
- The code is written to be clean, modular, and easily adaptable:
  - Adding a new source only requires a new `scrape_<source>()` function that returns a list of review objects.
