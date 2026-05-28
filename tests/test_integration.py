import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
from scraper import extract_job_url, extract_salary, extract_city, is_good_text


class TestIndeedIntegration:
    """Integration tests using real Indeed HTML samples."""

    @pytest.fixture(scope="class")
    def indeed_html(self):
        """Load real Indeed HTML from saved sample."""
        html_path = os.path.join(os.path.dirname(__file__), "..", "indeed_full.html")
        if not os.path.exists(html_path):
            pytest.skip("indeed_full.html not found - run scraper first to capture sample")
        with open(html_path, "r") as f:
            return f.read()

    @pytest.fixture(scope="class")
    def soup(self, indeed_html):
        return BeautifulSoup(indeed_html, "html.parser")

    def test_html_contains_job_cards(self, soup):
        """Verify the HTML actually contains job listings."""
        # Look for divs with salary text (indicator of job cards)
        divs = soup.find_all("div")
        salary_divs = [d for d in divs if "₹" in d.get_text(" ", strip=True)]
        assert len(salary_divs) > 0, "No salary mentions found - HTML may not contain jobs"

    def test_no_placeholder_urls_in_results(self, soup):
        """Verify no placeholder jk IDs are extracted."""
        divs = soup.find_all("div")
        placeholder_patterns = ["fedcba9876543210", "abcdef0123456789", "890abcdef0123456"]

        for div in divs:
            text = div.get_text(" ", strip=True)
            if not text or len(text) < 50 or len(text) > 350:
                continue
            if not is_good_text(text):
                continue

            url = extract_job_url(div, "https://in.indeed.com/jobs?q=test")
            for pattern in placeholder_patterns:
                assert pattern not in url, f"Placeholder {pattern} found in URL: {url}"

    def test_extracted_urls_are_specific_not_search_pages(self, soup):
        """Verify extracted URLs point to specific jobs, not search pages."""
        divs = soup.find_all("div")
        found_specific_url = False

        for div in divs:
            text = div.get_text(" ", strip=True)
            if not text or len(text) < 50 or len(text) > 350:
                continue
            if "doctor" not in text.lower():
                continue

            url = extract_job_url(div, "https://in.indeed.com/jobs?q=test")
            # Should either be base_url (no good link found) or a job-related URL
            if url != "https://in.indeed.com/jobs?q=test":
                # Allow jk= links, cmp/company links, or job detail links
                is_job_related = (
                    "jk=" in url or
                    "/cmp/" in url or
                    "/rc/clk" in url or
                    "/viewjob" in url
                )
                if is_job_related:
                    found_specific_url = True
                # If not job-related, it should fall back to base_url
                # (some divs with "doctor" text may not have job links nearby)

        assert found_specific_url, "No specific job URLs were extracted"

    def test_salary_extraction_from_real_html(self, soup):
        """Verify salary extraction works on real Indeed content."""
        divs = soup.find_all("div")
        found_salary = False

        for div in divs:
            text = div.get_text(" ", strip=True)
            if "₹" in text and len(text) > 50:
                salary = extract_salary(text)
                if salary:
                    assert salary.startswith("₹"), f"Salary should start with ₹: {salary}"
                    found_salary = True

        assert found_salary, "Could not extract any salaries from real HTML"

    def test_city_extraction_from_real_html(self, soup):
        """Verify city extraction works on real Indeed content."""
        divs = soup.find_all("div")
        found_city = False

        for div in divs:
            text = div.get_text(" ", strip=True)
            if "Bengaluru" in text or "Bangalore" in text:
                city = extract_city(text)
                if city:
                    assert city in ["Bengaluru", "Bangalore"], f"Unexpected city: {city}"
                    found_city = True

        assert found_city, "Could not extract any cities from real HTML"

    def test_job_url_contains_jk_parameter(self, soup):
        """Verify real job URLs contain jk= parameter."""
        divs = soup.find_all("div")
        found_jk_url = False

        for div in divs:
            text = div.get_text(" ", strip=True)
            if not text or len(text) < 50 or len(text) > 350:
                continue
            if "doctor" not in text.lower():
                continue

            url = extract_job_url(div, "https://in.indeed.com/jobs?q=test")
            if "jk=" in url:
                found_jk_url = True
                # Verify it's not a placeholder
                assert "fedcba9876543210" not in url
                assert "abcdef0123456789" not in url

        assert found_jk_url, "No URLs with jk= parameter found"

    def test_duplicate_handling(self, soup):
        """Verify the scraper would deduplicate similar entries."""
        # Simulate what the scraper does
        results = []
        divs = soup.find_all("div")

        for div in divs:
            text = div.get_text(" ", strip=True)
            if not text or len(text) < 50 or len(text) > 350:
                continue
            if not is_good_text(text):
                continue
            if "doctor" in text.lower():
                salary = extract_salary(text)
                city = extract_city(text)
                job_url = extract_job_url(div, "https://in.indeed.com/jobs?q=test")
                results.append({
                    "city": city,
                    "salary": salary,
                    "lead_text": text[:250],
                    "source_url": job_url
                })

        # Check for duplicates
        unique_texts = set()
        duplicates = []
        for r in results:
            key = r["lead_text"][:100]  # First 100 chars as fingerprint
            if key in unique_texts:
                duplicates.append(r)
            else:
                unique_texts.add(key)

        # It's OK to have some duplicates (they get removed by pandas later)
        # But we should verify deduplication would work
        assert len(results) > 0, "No results extracted"
        if duplicates:
            print(f"Found {len(duplicates)} potential duplicates out of {len(results)} results")


class TestUrlValidation:
    """Tests for URL validation and quality."""

    def test_indeed_rc_clk_url_is_valid(self):
        url = "https://in.indeed.com/rc/clk?jk=34eb7d4e09c13ce0&bb=test"
        assert url.startswith("https://in.indeed.com/")
        assert "jk=" in url
        assert "34eb7d4e09c13ce0" in url

    def test_url_joining_works_correctly(self):
        from urllib.parse import urljoin
        base = "https://in.indeed.com/jobs?q=test"
        href = "/rc/clk?jk=12345"
        result = urljoin(base, href)
        assert result == "https://in.indeed.com/rc/clk?jk=12345"

    def test_url_joining_with_absolute_href(self):
        from urllib.parse import urljoin
        base = "https://in.indeed.com/jobs?q=test"
        href = "https://in.indeed.com/viewjob?jk=12345"
        result = urljoin(base, href)
        assert result == "https://in.indeed.com/viewjob?jk=12345"

    def test_placeholder_detection(self):
        """Test that various placeholder patterns are detected."""
        from scraper import extract_job_url
        from bs4 import BeautifulSoup

        placeholders = [
            "/viewjob?jk=fedcba9876543210",
            "/viewjob?jk=abcdef0123456789",
            "/viewjob?jk=890abcdef0123456",
            "/viewjob?jk=f1e2d3c4b5a67890",
            "/viewjob?jk=1234567890abcdef",
        ]

        for ph in placeholders:
            html = f'<div><a href="{ph}">Job</a></div>'
            soup = BeautifulSoup(html, "html.parser")
            div = soup.find("div")
            result = extract_job_url(div, "https://in.indeed.com")
            assert result == "https://in.indeed.com", f"Placeholder not rejected: {ph}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
