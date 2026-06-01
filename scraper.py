import asyncio
import pandas as pd
import re
import json
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
    "locum",
    "duty",
    "consultant",
    "specialist",
    "resident",
    "physician",
    "surgeon",
    "anesthetist",
    "pathologist",
    "radiologist",
    "pediatrician",
    "gynecologist",
    "orthopedic",
    "cardiologist",
    "neurologist",
    "dermatologist",
    "ent",
    "ophthalmologist",
    "mbbs",
    "md",
    "ms",
    "dnb",
    "dm",
    "mch",
    "technician",
    "therapist",
    "pharmacist"
]

BAD_PATTERNS = [
    "skip to",
    "salary search results",  # Only filter actual salary-search pages, not card links
    "privacy policy",
    "cookie settings",
    "sign in to view",
    "pagination",
    "sort by",
    "main content",
    "jobs?q=",
    "people also searched",
    "get email updates",
    "career advice",
    "loading save-icon",
    "page not found",
    "404",
    "access denied",
    "blocked",
    "captcha",
    "cloudflare"
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


def extract_docthub_jobs(soup, base_url, seen_jks=None):
    """Extract job postings from DoctHub HTML."""
    jobs = []
    if seen_jks is None:
        seen_jks = set()
    
    # DoctHub uses article cards with job listings
    for article in soup.find_all("article", class_=lambda x: x and "job-card" in x):
        try:
            # Extract job title
            title_elem = article.find("h2") or article.find("h3") or article.find("a", class_=lambda x: x and "title" in x)
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract hospital/company
            company_elem = article.find("span", class_=lambda x: x and "company" in x) or \
                          article.find("div", class_=lambda x: x and "company" in x)
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            # Extract location
            loc_elem = article.find("span", class_=lambda x: x and "location" in x) or \
                       article.find("div", class_=lambda x: x and "location" in x)
            location = loc_elem.get_text(strip=True) if loc_elem else ""
            
            # Extract salary
            salary_elem = article.find("span", class_=lambda x: x and "salary" in x) or \
                          article.find("div", class_=lambda x: x and "salary" in x)
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Extract job type
            type_elem = article.find("span", class_=lambda x: x and "job-type" in x) or \
                        article.find("div", class_=lambda x: x and "job-type" in x)
            job_type = type_elem.get_text(strip=True) if type_elem else ""
            
            # Extract job URL
            link_elem = article.find("a", href=True)
            job_url = urljoin(base_url, link_elem["href"]) if link_elem else base_url
            
            # Generate unique ID from URL
            jk_id = link_elem["href"].split("/")[-1] if link_elem else ""
            if jk_id in seen_jks:
                continue
            seen_jks.add(jk_id)
            
            # Get full text for keyword filtering
            text = article.get_text(" ", strip=True)
            if not any(k.lower() in text.lower() for k in KEYWORDS):
                continue
            if not is_good_text(text):
                continue
            
            enriched = enrich_lead(
                text,
                source_url=job_url,
                pre_hospital=company,
                pre_city=location,
                pre_salary=salary,
                pre_hiring_type=job_type,
                pre_role=title,
            )
            jobs.append(enriched)
        except Exception as e:
            continue
    
    return jobs


def extract_drlogy_jobs(soup, base_url, seen_jks=None):
    """Extract job postings from DrLogy HTML."""
    jobs = []
    if seen_jks is None:
        seen_jks = set()
    
    # DrLogy uses div cards with job listings
    for card in soup.find_all("div", class_=lambda x: x and "job-card" in x):
        try:
            # Extract job title
            title_elem = card.find("h3") or card.find("h4") or card.find("a", class_=lambda x: x and "title" in x)
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract hospital/company
            company_elem = card.find("span", class_=lambda x: x and "hospital" in x) or \
                           card.find("div", class_=lambda x: x and "hospital" in x)
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            # Extract location
            loc_elem = card.find("span", class_=lambda x: x and "location" in x) or \
                       card.find("div", class_=lambda x: x and "location" in x)
            location = loc_elem.get_text(strip=True) if loc_elem else ""
            
            # Extract salary
            salary_elem = card.find("span", class_=lambda x: x and "salary" in x) or \
                          card.find("div", class_=lambda x: x and "salary" in x)
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Extract experience
            exp_elem = card.find("span", class_=lambda x: x and "experience" in x)
            experience = exp_elem.get_text(strip=True) if exp_elem else ""
            
            # Extract job URL
            link_elem = card.find("a", href=True)
            job_url = urljoin(base_url, link_elem["href"]) if link_elem else base_url
            
            # Generate unique ID
            jk_id = link_elem["href"].split("/")[-1] if link_elem else ""
            if jk_id in seen_jks:
                continue
            seen_jks.add(jk_id)
            
            # Get full text
            text = card.get_text(" ", strip=True)
            if not any(k.lower() in text.lower() for k in KEYWORDS):
                continue
            if not is_good_text(text):
                continue
            
            # Combine experience with text for better extraction
            full_text = f"{text} Experience: {experience}"
            
            enriched = enrich_lead(
                full_text,
                source_url=job_url,
                pre_hospital=company,
                pre_city=location,
                pre_salary=salary,
                pre_role=title,
            )
            jobs.append(enriched)
        except Exception as e:
            continue
    
    return jobs


def extract_foundit_jobs(soup, base_url, seen_jks=None):
    """Extract job postings from FoundIt (Monster) HTML."""
    jobs = []
    if seen_jks is None:
        seen_jks = set()
    
    # FoundIt uses div job cards
    for card in soup.find_all("div", class_=lambda x: x and ("job-card" in x or "srp-job" in x)):
        try:
            # Extract job title
            title_elem = card.find("h3") or card.find("a", class_=lambda x: x and "title" in x)
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract company
            company_elem = card.find("span", class_=lambda x: x and "company" in x) or \
                           card.find("div", class_=lambda x: x and "company" in x)
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            # Extract location
            loc_elem = card.find("span", class_=lambda x: x and "location" in x) or \
                       card.find("div", class_=lambda x: x and "location" in x)
            location = loc_elem.get_text(strip=True) if loc_elem else ""
            
            # Extract experience
            exp_elem = card.find("span", class_=lambda x: x and "experience" in x)
            experience = exp_elem.get_text(strip=True) if exp_elem else ""
            
            # Extract job URL
            link_elem = card.find("a", href=True)
            job_url = urljoin(base_url, link_elem["href"]) if link_elem else base_url
            
            # Generate unique ID
            jk_id = link_elem["href"].split("/")[-1] if link_elem else ""
            if jk_id in seen_jks:
                continue
            seen_jks.add(jk_id)
            
            # Get full text
            text = card.get_text(" ", strip=True)
            if not any(k.lower() in text.lower() for k in KEYWORDS):
                continue
            if not is_good_text(text):
                continue
            
            full_text = f"{text} Experience: {experience}"
            
            enriched = enrich_lead(
                full_text,
                source_url=job_url,
                pre_hospital=company,
                pre_city=location,
                pre_role=title,
            )
            jobs.append(enriched)
        except Exception as e:
            continue
    
    return jobs


def extract_locumdoctors_jobs(soup, base_url, seen_jks=None):
    """Extract job postings from LocumDoctors.co.in HTML."""
    jobs = []
    if seen_jks is None:
        seen_jks = set()
    
    # LocumDoctors uses table rows or div cards
    for row in soup.find_all("tr", class_=lambda x: x and "job" in x) or \
                soup.find_all("div", class_=lambda x: x and "job" in x):
        try:
            # Extract job title
            title_elem = row.find("h3") or row.find("h4") or row.find("a")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract hospital/company
            company_elem = row.find("td", class_=lambda x: x and "hospital" in x) or \
                          row.find("div", class_=lambda x: x and "hospital" in x)
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            # Extract location
            loc_elem = row.find("td", class_=lambda x: x and "location" in x) or \
                       row.find("div", class_=lambda x: x and "location" in x)
            location = loc_elem.get_text(strip=True) if loc_elem else ""
            
            # Extract job URL
            link_elem = row.find("a", href=True)
            job_url = urljoin(base_url, link_elem["href"]) if link_elem else base_url
            
            # Generate unique ID
            jk_id = link_elem["href"].split("/")[-1] if link_elem else ""
            if jk_id in seen_jks:
                continue
            seen_jks.add(jk_id)
            
            # Get full text
            text = row.get_text(" ", strip=True)
            if not any(k.lower() in text.lower() for k in KEYWORDS):
                continue
            if not is_good_text(text):
                continue
            
            enriched = enrich_lead(
                text,
                source_url=job_url,
                pre_hospital=company,
                pre_city=location,
                pre_role=title,
            )
            jobs.append(enriched)
        except Exception as e:
            continue
    
    return jobs


def extract_trakstar_jobs(soup, base_url, seen_jks=None):
    """Extract job postings from Trakstar career pages (Apollo, Fortis)."""
    jobs = []
    if seen_jks is None:
        seen_jks = set()
    
    # Trakstar uses div job listings
    for listing in soup.find_all("div", class_=lambda x: x and ("job" in x or "opening" in x)):
        try:
            # Extract job title
            title_elem = listing.find("h3") or listing.find("h2") or listing.find("a")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract location
            loc_elem = listing.find("span", class_=lambda x: x and "location" in x) or \
                       listing.find("div", class_=lambda x: x and "location" in x)
            location = loc_elem.get_text(strip=True) if loc_elem else ""
            
            # Extract department
            dept_elem = listing.find("span", class_=lambda x: x and "department" in x) or \
                        listing.find("div", class_=lambda x: x and "department" in x)
            department = dept_elem.get_text(strip=True) if dept_elem else ""
            
            # Extract job URL
            link_elem = listing.find("a", href=True)
            job_url = urljoin(base_url, link_elem["href"]) if link_elem else base_url
            
            # Generate unique ID
            jk_id = link_elem["href"].split("/")[-1] if link_elem else ""
            if jk_id in seen_jks:
                continue
            seen_jks.add(jk_id)
            
            # Get full text
            text = listing.get_text(" ", strip=True)
            if not any(k.lower() in text.lower() for k in KEYWORDS):
                continue
            if not is_good_text(text):
                continue
            
            # Extract hospital name from URL
            hospital = ""
            if "apollo" in base_url.lower():
                hospital = "Apollo Hospitals"
            elif "fortis" in base_url.lower():
                hospital = "Fortis Healthcare"
            
            full_text = f"{text} Department: {department}"
            
            enriched = enrich_lead(
                full_text,
                source_url=job_url,
                pre_hospital=hospital,
                pre_city=location,
                pre_role=title,
            )
            jobs.append(enriched)
        except Exception as e:
            continue
    
    return jobs


def extract_jobhai_jobs(soup, base_url, seen_jks=None):
    """Extract job postings from JobHai HTML."""
    jobs = []
    if seen_jks is None:
        seen_jks = set()
    
    # JobHai uses div job cards
    for card in soup.find_all("div", class_=lambda x: x and "job-card" in x):
        try:
            # Extract job title
            title_elem = card.find("h3") or card.find("h2") or card.find("a")
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract company
            company_elem = card.find("span", class_=lambda x: x and "company" in x) or \
                           card.find("div", class_=lambda x: x and "company" in x)
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            # Extract location
            loc_elem = card.find("span", class_=lambda x: x and "location" in x) or \
                       card.find("div", class_=lambda x: x and "location" in x)
            location = loc_elem.get_text(strip=True) if loc_elem else ""
            
            # Extract salary
            salary_elem = card.find("span", class_=lambda x: x and "salary" in x) or \
                          card.find("div", class_=lambda x: x and "salary" in x)
            salary = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Extract job URL
            link_elem = card.find("a", href=True)
            job_url = urljoin(base_url, link_elem["href"]) if link_elem else base_url
            
            # Generate unique ID
            jk_id = link_elem["href"].split("/")[-1] if link_elem else ""
            if jk_id in seen_jks:
                continue
            seen_jks.add(jk_id)
            
            # Get full text
            text = card.get_text(" ", strip=True)
            if not any(k.lower() in text.lower() for k in KEYWORDS):
                continue
            if not is_good_text(text):
                continue
            
            enriched = enrich_lead(
                text,
                source_url=job_url,
                pre_hospital=company,
                pre_city=location,
                pre_salary=salary,
                pre_role=title,
            )
            jobs.append(enriched)
        except Exception as e:
            continue
    
    return jobs


def extract_job_ages_from_html(html):
    """Extract jobKey -> age mapping from Indeed's embedded JSON in <script> tags.
    
    Indeed stores job dates in window.mosaic.providerData['mosaic-provider-jobcards']
    under a 'results' array with 'jobKey' and 'formattedRelativeTime' fields.
    """
    ages = {}
    
    # Extract the mosaic-provider-jobcards providerData JSON block
    match = re.search(
        r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.*?\});\s*\n\s*window\.mosaic\.providerData\["',
        html, re.DOTALL
    )
    if not match:
        match = re.search(
            r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.*?\});',
            html, re.DOTALL
        )
    
    if not match:
        return ages
    
    data = match.group(1)
    
    # Find the 'results' array that contains job objects with formattedRelativeTime
    for arr_match in re.finditer(r'"results"\s*:\s*(\[)', data):
        start = arr_match.start(1)
        # Find matching close bracket by tracking depth
        depth = 1
        in_string = False
        escape = False
        for i, c in enumerate(data[start + 1:], start + 1):
            if escape:
                escape = False
                continue
            if c == '\\':
                escape = True
                continue
            if c == '"' and not escape:
                in_string = not in_string
                continue
            if not in_string:
                if c == '[':
                    depth += 1
                elif c == ']':
                    depth -= 1
                    if depth == 0:
                        arr_content = data[start:i + 1]
                        # Extract jobKey -> formattedRelativeTime pairs from this array
                        job_keys = re.findall(r'"jobKey":"([a-f0-9]+)"', arr_content)
                        times = re.findall(r'"formattedRelativeTime":"([^"]+)"', arr_content)
                        if len(job_keys) == len(times) and len(job_keys) > 0:
                            for jk, time in zip(job_keys, times):
                                ages[jk] = time
                        break
    
    return ages


def extract_indeed_jobs(soup, base_url, seen_jks=None, job_ages=None):
    """Extract job postings from Indeed HTML using structured data attributes.

    Indeed renders job cards with data-testid attributes that hold clean values
    for company name, location, salary, etc. We extract those directly instead
    of flattening the card to text and regex-parsing.
    """
    jobs = []
    if seen_jks is None:
        seen_jks = set()
    if job_ages is None:
        job_ages = {}

    # Find every job-link anchor that carries data-jk
    for link in soup.find_all("a", {"data-jk": True}):
        jk_id = link.get("data-jk", "").strip()
        if not jk_id:
            continue

        # Skip placeholders and duplicates
        if jk_id in ("fedcba9876543210", "abcdef0123456789"):
            continue
        if jk_id in seen_jks:
            continue
        seen_jks.add(jk_id)

        # Walk up to the card container (<li> or div.cardOutline)
        container = link
        for _ in range(15):
            if container is None:
                break
            cls = container.get("class", [])
            if container.name == "li" or (cls and "cardOutline" in cls):
                break
            container = container.parent

        if container is None:
            continue

        # --- Structured field extraction ---
        # Title
        title = ""
        title_span = link.find("span", id=lambda x: x and x.startswith("jobTitle-"))
        if title_span:
            title = title_span.get_text(strip=True)
        if not title:
            title = link.get_text(strip=True)

        # Company name
        company = ""
        company_elem = container.find("span", {"data-testid": "company-name"})
        if company_elem:
            company = company_elem.get_text(strip=True)

        # Location
        location = ""
        loc_elem = container.find("div", {"data-testid": "text-location"})
        if loc_elem:
            location = loc_elem.get_text(strip=True)

        # Salary
        salary = ""
        salary_elem = container.find("li", {"data-testid": "attribute_snippet_testid salary-snippet-container"})
        if salary_elem:
            salary = salary_elem.get_text(strip=True)
        if not salary:
            # Fallback: any span with css-zydy3i that contains ₹
            for span in container.find_all("span", class_="css-zydy3i"):
                txt = span.get_text(strip=True)
                if "₹" in txt:
                    salary = txt
                    break

        # Job type / attributes (Full-time, Day Shift, etc.)
        job_type = ""
        JOB_TYPE_KEYWORDS = [
            "full-time", "part-time", "contract", "temporary", "internship",
            "flexible", "day shift", "night shift", "rotational shift",
            "morning shift", "evening shift", "weekend shift", "locum",
            "urgent", "immediate joining", "immediate",
        ]
        for li in container.find_all("li", class_="mosaic-provider-jobcards-fswglz"):
            txt = li.get_text(strip=True)
            if txt and not txt.startswith("₹") and any(jt in txt.lower() for jt in JOB_TYPE_KEYWORDS):
                job_type = txt
                break
        # Fallback: scan any span with css-zydy3i for job-type keywords
        if not job_type:
            for span in container.find_all("span", class_="css-zydy3i"):
                txt = span.get_text(strip=True)
                if txt and not txt.startswith("₹") and any(jt in txt.lower() for jt in JOB_TYPE_KEYWORDS):
                    job_type = txt
                    break

        # Date text
        date_text = ""
        # 1. Try the hidden JSON ages first (most reliable)
        if jk_id in job_ages:
            date_text = job_ages[jk_id]
        # 2. Fallback: search container text for date patterns
        if not date_text:
            container_text = container.get_text(" ", strip=True).lower()
            for pattern in [
                r'(\d+)\+?\s+day[s]?\s+ago',
                r'(\d+)\s+hour[s]?\s+ago',
                r'today',
                r'just\s+posted',
            ]:
                m = re.search(pattern, container_text, re.IGNORECASE)
                if m:
                    date_text = m.group(0)
                    break

        # Build the flat text for keyword / quality filtering
        text = container.get_text(" ", strip=True)
        if not any(k.lower() in text.lower() for k in KEYWORDS):
            continue
        if not is_good_text(text):
            continue

        # Build job URL
        href = link.get("href", "")
        job_url = urljoin(base_url, href) if href else base_url

        # Pass structured fields to enrich_lead so it doesn't have to guess
        enriched = enrich_lead(
            text,
            source_url=job_url,
            date_text=date_text,
            pre_hospital=company,
            pre_city=location,
            pre_salary=salary,
            pre_hiring_type=job_type,
            pre_role=title,
        )
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
                    job_ages = extract_job_ages_from_html(html)
                    indeed_jobs = extract_indeed_jobs(soup, url, seen_jks, job_ages)
                    results.extend(indeed_jobs)
                elif "docthub.com" in url:
                    docthub_jobs = extract_docthub_jobs(soup, url, seen_jks)
                    results.extend(docthub_jobs)
                elif "drlogy.com" in url:
                    drlogy_jobs = extract_drlogy_jobs(soup, url, seen_jks)
                    results.extend(drlogy_jobs)
                elif "foundit.in" in url:
                    foundit_jobs = extract_foundit_jobs(soup, url, seen_jks)
                    results.extend(foundit_jobs)
                elif "locumdoctors.co.in" in url:
                    locum_jobs = extract_locumdoctors_jobs(soup, url, seen_jks)
                    results.extend(locum_jobs)
                elif "trakstar.com" in url:
                    trakstar_jobs = extract_trakstar_jobs(soup, url, seen_jks)
                    results.extend(trakstar_jobs)
                elif "jobhai.com" in url:
                    jobhai_jobs = extract_jobhai_jobs(soup, url, seen_jks)
                    results.extend(jobhai_jobs)
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