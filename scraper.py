import asyncio
import pandas as pd
import re
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
from extractor import enrich_lead

# Read URLs from urls.txt
with open("urls.txt", "r") as f:
    URLS = [line.strip() for line in f if line.strip()]

KEYWORDS = [
    "doctor",
    "duty doctor",
    "medical officer",
    "resident medical officer",
    "RMO",
    "BAMS",
    "BHMS",
    "nurse",
    "locum"
]

BAD_PATTERNS = [
    "skip to",
    "salary search",
    "privacy",
    "cookie",
    "sign in",
    "pagination",
    "sort by",
    "main content",
    "jobs?q=",
    "people also searched",
    "get email updates",
    "career advice",
    "loading save-icon"
]

results = []


def is_good_text(text):

    text_lower = text.lower()

    for bad in BAD_PATTERNS:
        if bad in text_lower:
            return False

    return True


def extract_salary(text):

    match = re.search(r'₹[\d,]+(?:\.\d+)?(?:\s*-\s*₹[\d,]+(?:\.\d+)?)?', text)

    if match:
        return match.group(0)

    return ""


def extract_city(text):

    cities = [
        "Bengaluru",
        "Bangalore",
        "Hyderabad",
        "Delhi",
        "Mumbai",
        "Pune",
        "Chennai",
        "Kolkata",
        "Lucknow",
        "Jaipur"
    ]

    for city in cities:
        if city.lower() in text.lower():
            return city

    return ""


from urllib.parse import urljoin


def extract_indeed_jobs(soup, base_url, seen_jks=None):
    """Extract job postings from Indeed HTML by starting from job links."""
    jobs = []
    if seen_jks is None:
        seen_jks = set()

    # Find all links that look like job postings (rc/clk with jk=)
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if "/rc/clk" not in href or "jk=" not in href:
            continue

        # Extract jk ID to deduplicate
        jk_match = re.search(r'jk=([a-f0-9]+)', href)
        if not jk_match:
            continue
        jk_id = jk_match.group(1)

        # Skip placeholders and already-seen jobs
        if jk_id in ("fedcba9876543210", "abcdef0123456789"):
            continue
        if jk_id in seen_jks:
            continue
        seen_jks.add(jk_id)

        # Climb up to find the job card container
        container = link.parent
        for _ in range(5):
            if container is None:
                break
            text = container.get_text(" ", strip=True)
            if len(text) >= 50 and len(text) <= 500:
                break
            container = container.parent

        if container is None:
            continue

        text = container.get_text(" ", strip=True)

        # Filter by keywords
        if not any(k.lower() in text.lower() for k in KEYWORDS):
            continue

        if not is_good_text(text):
            continue

        # Extract posting date text from the container
        date_text = ""
        for elem in container.find_all(["span", "div", "td"]):
            elem_text = elem.get_text(strip=True).lower()
            if any(marker in elem_text for marker in ["ago", "today", "just posted", "posted"]):
                date_text = elem.get_text(strip=True)
                break

        job_url = urljoin(base_url, href)
        enriched = enrich_lead(text, job_url, date_text=date_text)
        jobs.append(enriched)

    return jobs


def extract_job_url(element, base_url):
    """Find the most specific job posting URL near the matched element."""

    # If this is a proper job card container (like Indeed's <li>), only look inside it.
    # Don't climb to ancestors or siblings — that leads to cross-contamination.
    is_job_card = element.name in ("li", "article", "section")

    if is_job_card:
        candidates = [element]
    else:
        # Gather candidate elements: element, ancestors up to 5 levels, and siblings
        candidates = []
        current = element
        for _ in range(6):
            if current is None:
                break
            candidates.append(current)
            current = current.parent

        # Also check siblings of the element and its parent
        if element.next_sibling:
            candidates.append(element.next_sibling)
        if element.previous_sibling:
            candidates.append(element.previous_sibling)
        if element.parent:
            if element.parent.next_sibling:
                candidates.append(element.parent.next_sibling)
            if element.parent.previous_sibling:
                candidates.append(element.parent.previous_sibling)

    # Collect all unique hrefs from candidate elements
    hrefs = set()
    for element in candidates:
        if not hasattr(element, "find_all"):
            continue
        for link in element.find_all("a", href=True):
            href = link.get("href", "").strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            hrefs.add(href)

    if not hrefs:
        return base_url

    # Filter out known placeholder/template URLs
    PLACEHOLDER_PATTERNS = [
        "fedcba9876543210",  # Indeed template job ID (reverse sequential)
        "abcdef0123456789",  # Sequential hex
        "890abcdef0123456",  # Mixed sequential
        "f1e2d3c4b5a67890",  # Patterned hex
        "0000000000000000",
        "1234567890abcdef",
    ]

    def is_sequential_hex(jk_id):
        """Detect if a jk ID looks like a placeholder/sequential pattern."""
        if len(jk_id) != 16:
            return False
        # Check for reverse sequential (fedcba...)
        if jk_id == "fedcba9876543210":
            return True
        # Check for sequential hex (0123456789abcdef or variants)
        sorted_chars = ''.join(sorted(set(jk_id)))
        if len(sorted_chars) <= 8:  # Too few unique characters
            return True
        # Check for obvious patterns like abcd, 1234, etc.
        patterns = ['abcd', 'ef01', '2345', '6789', 'fedc', 'ba98', '7654', '3210']
        lower_id = jk_id.lower()
        for p in patterns:
            if p in lower_id:
                return True
        return False

    def is_placeholder(href):
        lower = href.lower()
        if any(p in lower for p in PLACEHOLDER_PATTERNS):
            return True
        # Extract jk= value and check if it's sequential hex
        import re
        jk_match = re.search(r'jk=([a-f0-9]{16})', lower)
        if jk_match:
            return is_sequential_hex(jk_match.group(1))
        return False

    # Score each href: higher = more likely to be a specific job page
    def score_href(href):
        score = 0
        lower = href.lower()
        full = urljoin(base_url, href)

        # Reject placeholders entirely
        if is_placeholder(href):
            return -9999

        # Indeed specific: links containing jk= or vjk= are SPECIFIC job pages
        if "jk=" in lower or "vjk=" in lower:
            score += 100
            # Prefer rc/clk links over viewjob (viewjob can be a template)
            if "/rc/clk" in lower:
                score += 50

        # Job-related keywords in URL
        job_keywords = ["job", "opening", "posting", "detail", "view", "apply", "vacancy", "position"]
        for kw in job_keywords:
            if kw in lower:
                score += 10

        # Penalize generic career/salary/guide pages
        bad_terms = ["page", "next", "prev", "search", "?q=", "jobs?q=", "career/", "salary", "guide", "how-to"]
        for bt in bad_terms:
            if bt in lower:
                score -= 40

        # Prefer absolute URLs
        if href.startswith("http"):
            score += 5

        # Penalize if it's exactly the base URL
        if full == base_url:
            score -= 30

        # Prefer longer, more specific paths
        path = full.replace(base_url, "")
        if len(path) > 20:
            score += 5

        return score

    scored = [(href, score_href(href)) for href in hrefs]
    scored.sort(key=lambda x: x[1], reverse=True)

    # If best score is negative (all placeholders), fall back to base_url
    if scored[0][1] < 0:
        return base_url

    best_href = scored[0][0]
    return urljoin(base_url, best_href)


async def main():

    # Track seen job IDs across ALL URLs to prevent duplicates
    seen_jks = set()

    async with AsyncWebCrawler() as crawler:

        for url in URLS:

            print(f"\nChecking: {url}")

            try:
                result = await crawler.arun(url=url)

                html = result.html

                soup = BeautifulSoup(html, "html.parser")

                # For Indeed: find all job links first, then extract text from their container
                if "indeed.com" in url:
                    indeed_jobs = extract_indeed_jobs(soup, url, seen_jks)
                    results.extend(indeed_jobs)
                else:
                    # For other sites, fall back to div-based scraping
                    job_elements = soup.find_all("div")

                    seen_texts = set()

                    for element in job_elements:

                        text = element.get_text(" ", strip=True)

                        if not text:
                            continue

                        # Ignore tiny/noisy content
                        if len(text) < 50 or len(text) > 500:
                            continue

                        if not is_good_text(text):
                            continue

                        # Match hiring keywords
                        if any(k.lower() in text.lower() for k in KEYWORDS):

                            # Skip if we've already seen very similar text
                            text_fingerprint = text[:100].lower().strip()
                            if text_fingerprint in seen_texts:
                                continue
                            seen_texts.add(text_fingerprint)

                            from extractor import enrich_lead
                            enriched = enrich_lead(text, extract_job_url(element, url))
                            results.append(enriched)

            except Exception as e:
                print(f"Error for {url}: {e}")

    # Create dataframe
    df = pd.DataFrame(results)

    # Remove duplicates
    df.drop_duplicates(inplace=True)

    # Save CSV
    df.to_csv("daily_leads.csv", index=False)

    print("\n====================")
    print("TOP LEADS")
    print("====================\n")

    print(df.head(20))

    print(f"\nSaved {len(df)} cleaned leads to daily_leads.csv")


asyncio.run(main())