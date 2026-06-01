"""
Playwright-based scraper for JavaScript-rendered job sites.
Handles DoctHub, DrLogy, FoundIt, Trakstar career pages, and JobHai.
"""

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


KEYWORDS = [
    "doctor", "duty doctor", "medical officer", "resident medical officer",
    "RMO", "BAMS", "BHMS", "nurse", "locum", "duty", "consultant",
    "specialist", "resident", "physician", "surgeon", "anesthetist",
    "pathologist", "radiologist", "radiology", "pediatrician", "gynecologist",
    "orthopedic", "cardiologist", "neurologist", "dermatologist",
    "ent", "ophthalmologist", "mbbs", "md", "ms", "dnb", "dm",
    "mch", "technician", "therapist", "pharmacist"
]


def is_good_text(text):
    text_lower = text.lower()
    bad_patterns = [
        "skip to", "privacy policy", "cookie settings", "sign in to view",
        "pagination", "sort by", "main content", "page not found", "404",
        "access denied", "blocked", "captcha", "cloudflare"
    ]
    for bad in bad_patterns:
        if bad in text_lower:
            return False
    return True


def extract_docthub_jobs(soup, base_url, seen_urls=None):
    jobs = []
    if seen_urls is None:
        seen_urls = set()
    
    # DoctHub structure: <li class="...all_jobs_listing_card...">
    #   <a class="cursor-pointer..." href="/job-id">
    #     <div class="all_jobs_listing_card_info">...</div>
    #     <div class="all_jobs_listing_card_footer">...</div>
    #   </a>
    # </li>
    # Find the <li> cards directly
    cards = soup.find_all("li", class_=lambda x: x and "all_jobs_listing_card" in str(x))
    
    for card in cards:
        try:
            # Find the <a> inside the <li>
            link_elem = card.find("a", href=True)
            if not link_elem or not link_elem.get("href"):
                continue
            
            job_url = urljoin(base_url, link_elem["href"])
            
            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)
            
            # Get text from the card
            text = card.get_text(" ", strip=True)
            if not any(k.lower() in text.lower() for k in KEYWORDS):
                continue
            if not is_good_text(text):
                continue
            
            # Extract title from first meaningful line
            title = ""
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if lines:
                title = lines[0]
            
            # Look for location text (often ends with state name)
            location = ""
            loc_match = re.search(r'([A-Za-z\s]+,\s*[A-Za-z\s]+)$', text)
            if loc_match:
                location = loc_match.group(1).strip()
            
            # Look for salary patterns
            salary = ""
            sal_match = re.search(r'(\d+K\s*[-–]\s*\d+\.?\d*L?P?\.?M?|₹[\d,]+\s*[-–]\s*₹?[\d,]+)', text)
            if sal_match:
                salary = sal_match.group(1)
            
            from extractor import enrich_lead
            enriched = enrich_lead(
                text,
                source_url=job_url,
                pre_city=location,
                pre_salary=salary,
                pre_role=title,
            )
            jobs.append(enriched)
        except Exception:
            continue
    
    return jobs


def extract_drlogy_jobs(soup, base_url, seen_urls=None):
    jobs = []
    if seen_urls is None:
        seen_urls = set()
    
    # DrLogy: cards are divs with class "jobbs-wrapper", links are inside with class "jobbs-detail"
    for card in soup.find_all("div", class_=lambda x: x and "jobbs-wrapper" in str(x).lower()):
        try:
            link = card.find("a", class_=lambda x: x and "jobbs-detail" in str(x).lower(), href=True)
            if not link:
                continue
            
            job_url = urljoin(base_url, link["href"])
            
            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)
            
            text = card.get_text(" ", strip=True)
            if not any(k.lower() in text.lower() for k in KEYWORDS):
                continue
            if not is_good_text(text):
                continue
            
            # Extract title from card text (first line usually)
            title = ""
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if lines:
                title = lines[0]
            
            from extractor import enrich_lead
            enriched = enrich_lead(
                text,
                source_url=job_url,
                pre_role=title,
            )
            jobs.append(enriched)
        except Exception:
            continue
    
    return jobs


def extract_foundit_jobs(soup, base_url, seen_urls=None):
    jobs = []
    if seen_urls is None:
        seen_urls = set()
    
    for card in soup.find_all("div", class_=lambda x: x and ("job-card" in str(x).lower() or "srp-job" in str(x).lower())):
        try:
            title_elem = card.find("h3") or card.find("a", class_=lambda x: x and "title" in str(x).lower())
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            company_elem = card.find("span", class_=lambda x: x and "company" in str(x).lower()) or \
                           card.find("div", class_=lambda x: x and "company" in str(x).lower())
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            loc_elem = card.find("span", class_=lambda x: x and "location" in str(x).lower()) or \
                       card.find("div", class_=lambda x: x and "location" in str(x).lower())
            location = loc_elem.get_text(strip=True) if loc_elem else ""
            
            exp_elem = card.find("span", class_=lambda x: x and "experience" in str(x).lower()) or \
                       card.find("div", class_=lambda x: x and "experience" in str(x).lower())
            experience = exp_elem.get_text(strip=True) if exp_elem else ""
            
            link_elem = card.find("a", href=True)
            job_url = urljoin(base_url, link_elem["href"]) if link_elem else base_url
            
            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)
            
            text = card.get_text(" ", strip=True)
            if not any(k.lower() in text.lower() for k in KEYWORDS):
                continue
            if not is_good_text(text):
                continue
            
            full_text = f"{text} Experience: {experience}"
            
            from extractor import enrich_lead
            enriched = enrich_lead(
                full_text,
                source_url=job_url,
                pre_hospital=company,
                pre_city=location,
                pre_role=title,
            )
            jobs.append(enriched)
        except Exception:
            continue
    
    return jobs


def extract_trakstar_jobs(soup, base_url, seen_urls=None):
    jobs = []
    if seen_urls is None:
        seen_urls = set()
    
    hospital = ""
    if "apollo" in base_url.lower():
        hospital = "Apollo Hospitals"
    elif "fortis" in base_url.lower():
        hospital = "Fortis Healthcare"
    
    for listing in soup.find_all("div", class_=lambda x: x and ("job" in str(x).lower() or "opening" in str(x).lower())):
        try:
            title_elem = listing.find("h3") or listing.find("h2") or listing.find("a")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            loc_elem = listing.find("span", class_=lambda x: x and "location" in str(x).lower()) or \
                       listing.find("div", class_=lambda x: x and "location" in str(x).lower())
            location = loc_elem.get_text(strip=True) if loc_elem else ""
            
            dept_elem = listing.find("span", class_=lambda x: x and "department" in str(x).lower()) or \
                        listing.find("div", class_=lambda x: x and "department" in str(x).lower())
            department = dept_elem.get_text(strip=True) if dept_elem else ""
            
            link_elem = listing.find("a", href=True)
            job_url = urljoin(base_url, link_elem["href"]) if link_elem else base_url
            
            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)
            
            text = listing.get_text(" ", strip=True)
            if not any(k.lower() in text.lower() for k in KEYWORDS):
                continue
            if not is_good_text(text):
                continue
            
            full_text = f"{text} Department: {department}"
            
            from extractor import enrich_lead
            enriched = enrich_lead(
                full_text,
                source_url=job_url,
                pre_hospital=hospital,
                pre_city=location,
                pre_role=title,
            )
            jobs.append(enriched)
        except Exception:
            continue
    
    return jobs


def extract_jobhai_jobs(soup, base_url, seen_urls=None):
    jobs = []
    if seen_urls is None:
        seen_urls = set()
    
    for card in soup.find_all("div", class_=lambda x: x and "job-card" in str(x).lower()):
        try:
            title_elem = card.find("h3") or card.find("h2") or card.find("a")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            company_elem = card.find("span", class_=lambda x: x and "company" in str(x).lower()) or \
                           card.find("div", class_=lambda x: x and "company" in str(x).lower())
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            loc_elem = card.find("span", class_=lambda x: x and "location" in str(x).lower()) or \
                       card.find("div", class_=lambda x: x and "location" in str(x).lower())
            location = loc_elem.get_text(strip=True) if loc_elem else ""
            
            salary_elem = card.find("span", class_=lambda x: x and "salary" in str(x).lower()) or \
                          card.find("div", class_=lambda x: x and "salary" in str(x).lower())
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            link_elem = card.find("a", href=True)
            job_url = urljoin(base_url, link_elem["href"]) if link_elem else base_url
            
            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)
            
            text = card.get_text(" ", strip=True)
            if not any(k.lower() in text.lower() for k in KEYWORDS):
                continue
            if not is_good_text(text):
                continue
            
            from extractor import enrich_lead
            enriched = enrich_lead(
                text,
                source_url=job_url,
                pre_hospital=company,
                pre_city=location,
                pre_salary=salary,
                pre_role=title,
            )
            jobs.append(enriched)
        except Exception:
            continue
    
    return jobs


# ─── Router ───

SITE_EXTRACTORS = {
    "docthub.com": extract_docthub_jobs,
    "drlogy.com": extract_drlogy_jobs,
    "foundit.in": extract_foundit_jobs,
    "trakstar.com": extract_trakstar_jobs,
    "jobhai.com": extract_jobhai_jobs,
}


def _pick_extractor(url: str):
    for domain, extractor in SITE_EXTRACTORS.items():
        if domain in url.lower():
            return extractor
    return None


# ─── Main Playwright scraper ───

async def scrape_js_sites(urls: list, seen_urls: set = None) -> list:
    """
    Scrape JavaScript-rendered job sites using Playwright.

    Args:
        urls: List of URLs to scrape.
        seen_urls: Optional set of already-seen URLs for deduplication.

    Returns:
        List of enriched lead dicts.
    """
    if seen_urls is None:
        seen_urls = set()
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )

        for url in urls:
            extractor_fn = _pick_extractor(url)
            if extractor_fn is None:
                print(f"[Playwright] No extractor for {url}, skipping")
                continue

            print(f"[Playwright] Scraping: {url}")
            page = await context.new_page()
            try:
                # Use domcontentloaded for faster loading, then wait for JS
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)  # Give JS time to render content

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                jobs = extractor_fn(soup, url, seen_urls)
                results.extend(jobs)
                print(f"[Playwright]  → {len(jobs)} jobs from {url}")

            except PlaywrightTimeout:
                print(f"[Playwright]  ✗ Timeout: {url}")
            except Exception as e:
                print(f"[Playwright]  ✗ Error on {url}: {e}")
            finally:
                await page.close()

        await context.close()
        await browser.close()

    return results


if __name__ == "__main__":
    test_urls = [
        "https://jobs.docthub.com/all-jobs?job_type[]=locum",
    ]
    leads = asyncio.run(scrape_js_sites(test_urls))
    print(f"\nTotal leads: {len(leads)}")
    for lead in leads[:3]:
        print(lead)
