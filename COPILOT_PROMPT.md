# Medibrick Scraper Enhancement Prompt

## Context
I have a medical job scraper built with Python + Crawl4AI that works for Indeed and static sites. I need to add Playwright support for JavaScript-rendered sites.

## Problem
The current scraper in `scraper.py` works for Indeed but these new sources return empty HTML because they're JS-rendered:
- DoctHub (jobs.docthub.com)
- DrLogy (drlogy.com/jobs) 
- FoundIt (foundit.in)
- Apollo Trakstar (naukriapollo.hire.trakstar.com)
- Fortis Trakstar (fortishealthcare.hire.trakstar.com)
- JobHai (jobhai.com)

## Current Architecture

### `scraper.py`
- Uses Crawl4AI for Indeed and Manipal Hospitals (works)
- Reads URLs from `urls.txt`
- Extracts structured data using BeautifulSoup
- Saves to `daily_leads.csv`

### `extractor.py`
- Has `enrich_lead()` function that takes raw text + optional pre-extracted fields
- Returns dict with: hospital, role, department, city, salary, hiring_type, phone, email, contact, notes, date_posted, source_url

## Task

1. **Create `playwright_scraper.py`**:
   - Uses Playwright + async
   - Launches Chromium headless
   - Waits for JS to render (wait for selectors or timeout)
   - Extracts job cards using BeautifulSoup from rendered HTML
   - Returns list of enriched lead dicts
   - Handle errors gracefully (skip sites that fail)

2. **Update `scraper.py`**:
   - Import and call playwright_scraper after Crawl4AI URLs
   - Merge results from both scrapers
   - Remove JS-site extraction functions from scraper.py (they're not working)
   - Keep Indeed + Manipal on Crawl4AI (they work)

3. **Update `urls.txt`**:
   - Separate JS sites from static sites
   - Or keep all in one list and detect by domain

## File Structure
```
medibrick-leads/
├── scraper.py              # Update this
├── playwright_scraper.py   # Create this
├── extractor.py            # Keep as-is (enrich_lead function)
├── urls.txt                # Update this
├── daily_leads.csv         # Output
└── venv/                   # Virtual environment
```

## Key Requirements
- Must handle ARM64 Mac (Apple Silicon)
- Must be async (playwright.async_api)
- Must filter by medical keywords (duty doctor, locum, RMO, BAMS, etc.)
- Must use enrich_lead from extractor.py for consistency
- Must prevent duplicate URLs across sources

## Test Command
```bash
cd /Users/gagandeep/medibrick-leads
source venv/bin/activate
python scraper.py
```

Expected output: 55+ leads from Indeed + new leads from JS sites.
