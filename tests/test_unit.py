"""
Unit tests for scraper extractors.
These tests are PURE - they don't depend on live data or scraped CSVs.
They test your parsing logic with hardcoded inputs.
"""

import pytest
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import (
    is_good_text,
    extract_salary,
    extract_city,
    extract_job_url,
    KEYWORDS,
    BAD_PATTERNS,
)


class TestIsGoodText:
    """Tests for the is_good_text filter."""

    def test_allows_normal_job_text(self):
        text = "Duty Doctor required at Apollo Hospitals, Bengaluru. Salary ₹50,000 per month."
        assert is_good_text(text) is True

    def test_blocks_privacy_text(self):
        text = "Privacy policy and cookie settings for this website"
        assert is_good_text(text) is False

    def test_blocks_pagination(self):
        text = "Pagination: Page 1 of 10 results"
        assert is_good_text(text) is False

    def test_blocks_sign_in(self):
        text = "Please sign in to view more jobs"
        assert is_good_text(text) is False

    def test_case_insensitive_blocking(self):
        text = "PRIVACY POLICY"
        assert is_good_text(text) is False


class TestExtractSalary:
    """Tests for salary extraction."""

    def test_extracts_simple_salary(self):
        text = "Salary: ₹50,000 per month"
        assert extract_salary(text) == "₹50,000"

    def test_extracts_salary_range(self):
        text = "Pay: ₹30,000 - ₹65,000 a month"
        assert extract_salary(text) == "₹30,000 - ₹65,000"

    def test_returns_empty_when_no_salary(self):
        text = "Looking for a duty doctor at our hospital"
        assert extract_salary(text) == ""

    def test_extracts_first_salary_when_multiple(self):
        text = "₹40,000 - ₹50,000 or ₹60,000 for experienced"
        assert extract_salary(text) == "₹40,000 - ₹50,000"


class TestExtractCity:
    """Tests for city extraction."""

    def test_extracts_bengaluru(self):
        text = "Job location: Bengaluru, Karnataka"
        assert extract_city(text) == "Bengaluru"

    def test_returns_empty_for_unknown_city(self):
        text = "Job in Coimbatore, Tamil Nadu"
        assert extract_city(text) == ""

    def test_is_case_insensitive(self):
        text = "Location: BENGALURU"
        assert extract_city(text) == "Bengaluru"


class TestExtractJobUrl:
    """Tests for job URL extraction from HTML elements."""

    def create_div_with_link(self, html, base_url="https://in.indeed.com/jobs?q=test"):
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        return div, base_url

    def test_extracts_indeed_rc_clk_link(self):
        html = '<div><a href="/rc/clk?jk=34eb7d4e09c13ce0">Job Title</a></div>'
        div, base_url = self.create_div_with_link(html)
        result = extract_job_url(div, base_url)
        assert "jk=34eb7d4e09c13ce0" in result
        assert result.startswith("https://in.indeed.com")

    def test_rejects_placeholder_url(self):
        html = '<div><a href="/viewjob?jk=fedcba9876543210">Job Title</a></div>'
        div, base_url = self.create_div_with_link(html)
        result = extract_job_url(div, base_url)
        assert result == base_url

    def test_prefers_rc_clk_over_viewjob(self):
        html = '''
        <div>
            <a href="/viewjob?jk=fedcba9876543210">Template</a>
            <a href="/rc/clk?jk=34eb7d4e09c13ce0">Real Job</a>
        </div>
        '''
        div, base_url = self.create_div_with_link(html)
        result = extract_job_url(div, base_url)
        assert "rc/clk" in result
        assert "34eb7d4e09c13ce0" in result

    def test_falls_back_to_base_url_when_no_links(self):
        html = "<div>No links here</div>"
        div, base_url = self.create_div_with_link(html)
        result = extract_job_url(div, base_url)
        assert result == base_url

    def test_handles_relative_urls(self):
        html = '<div><a href="/jobs/detail/12345">Job</a></div>'
        div, base_url = self.create_div_with_link(html, "https://careers.manipalhospitals.com")
        result = extract_job_url(div, base_url)
        assert result == "https://careers.manipalhospitals.com/jobs/detail/12345"

    def test_looks_in_parent_elements(self):
        html = '''
        <div class="parent">
            <a href="/rc/clk?jk=34eb7d4e09c13ce0">Job</a>
            <div class="child">Job description text here</div>
        </div>
        '''
        soup = BeautifulSoup(html, "html.parser")
        child_div = soup.find("div", class_="child")
        result = extract_job_url(child_div, "https://in.indeed.com")
        assert "jk=34eb7d4e09c13ce0" in result


class TestKeywordsAndPatterns:
    """Tests for keyword matching and bad pattern filtering."""

    def test_keywords_match_expected_text(self):
        text = "We are hiring a duty doctor and a nurse"
        matches = [k for k in KEYWORDS if k.lower() in text.lower()]
        assert "doctor" in matches
        assert "duty doctor" in matches
        assert "nurse" in matches


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
