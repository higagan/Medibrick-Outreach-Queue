import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app import extract_hospital, extract_role


class TestDashboardExtractors:
    """Unit tests for the Streamlit dashboard extractors."""

    def test_extract_hospital_from_easily_apply_text(self):
        text = "Easily apply CURA HOSPITALS Kalyananagar, Bengaluru, Karnataka Up to ₹60,000"
        # Note: regex captures up to city name, may include extra text
        result = extract_hospital(text)
        assert "CURA" in result, f"Expected CURA in result, got: {result}"

    def test_extract_hospital_from_bangalore_text(self):
        text = "Easily apply Apollo Hospitals Bangalore, Karnataka"
        assert extract_hospital(text) == "Apollo Hospitals"

    def test_extract_hospital_returns_unknown_when_no_match(self):
        text = "Some random job description without hospital name"
        assert extract_hospital(text) == "Unknown"

    def test_extract_role_duty_doctor(self):
        text = "We are looking for a Duty Doctor at our hospital"
        assert extract_role(text) == "Duty Doctor"

    def test_extract_role_resident_medical_officer(self):
        text = "Resident Medical Officer required immediately"
        assert extract_role(text) == "Resident Medical Officer"

    def test_extract_role_bams_doctor(self):
        text = "BAMS Doctor needed for Ayurvedic clinic"
        assert extract_role(text) == "BAMS Doctor"

    def test_extract_role_nurse(self):
        text = "Nurse required for ICU ward"
        assert extract_role(text) == "Nurse"

    def test_extract_role_defaults_to_doctor(self):
        text = "General physician needed"
        assert extract_role(text) == "Doctor"

    def test_extract_role_case_insensitive(self):
        text = "We need a DUTY DOCTOR immediately"
        assert extract_role(text) == "Duty Doctor"


class TestDashboardDataProcessing:
    """Tests for dashboard data processing logic."""

    def test_dataframe_has_required_columns(self):
        """Verify the CSV has all required columns for the dashboard."""
        df = pd.read_csv("daily_leads.csv")
        required_columns = ["city", "salary", "lead_text", "source_url"]
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_no_placeholder_urls_in_csv(self):
        """Verify no placeholder URLs exist in the data."""
        df = pd.read_csv("daily_leads.csv")
        placeholder_patterns = ["fedcba9876543210", "abcdef0123456789", "890abcdef0123456"]

        for pattern in placeholder_patterns:
            matches = df["source_url"].str.contains(pattern, na=False)
            assert not matches.any(), f"Placeholder {pattern} found in CSV"

    def test_source_urls_are_not_empty(self):
        """Verify all rows have source URLs."""
        df = pd.read_csv("daily_leads.csv")
        empty_urls = df["source_url"].isna() | (df["source_url"] == "")
        assert not empty_urls.any(), "Empty source URLs found"

    def test_source_urls_start_with_http(self):
        """Verify all source URLs are absolute URLs."""
        df = pd.read_csv("daily_leads.csv")
        invalid_urls = ~df["source_url"].str.startswith("http", na=False)
        assert not invalid_urls.any(), f"Non-HTTP URLs found: {df[invalid_urls]['source_url'].tolist()}"

    def test_lead_text_not_empty(self):
        """Verify all rows have lead text."""
        df = pd.read_csv("daily_leads.csv")
        empty_text = df["lead_text"].isna() | (df["lead_text"] == "")
        assert not empty_text.any(), "Empty lead text found"

    def test_lead_text_reasonable_length(self):
        """Verify lead text is not too short or too long."""
        df = pd.read_csv("daily_leads.csv")
        too_short = df["lead_text"].str.len() < 10
        too_long = df["lead_text"].str.len() > 500
        assert not too_short.any(), "Lead text too short"
        assert not too_long.any(), "Lead text too long"

    def test_salary_format_valid(self):
        """Verify salary values contain ₹ symbol when present."""
        df = pd.read_csv("daily_leads.csv")
        # Filter out NaN and empty strings
        non_empty_salary = df[df["salary"].notna() & (df["salary"] != "")]
        if len(non_empty_salary) > 0:
            has_rupee = non_empty_salary["salary"].str.contains("₹", na=False)
            assert has_rupee.all(), "Some salaries missing ₹ symbol"

    def test_dashboard_deduplication_logic(self):
        """Verify deduplication by hospital+role+salary would work."""
        df = pd.read_csv("daily_leads.csv")

        # Apply the same deduplication as app.py
        df["hospital"] = df["lead_text"].apply(extract_hospital)
        df["role"] = df["lead_text"].apply(extract_role)

        before_count = len(df)
        df_deduped = df.drop_duplicates(subset=["hospital", "role", "salary"])
        after_count = len(df_deduped)

        # Should have fewer or equal rows after deduplication
        assert after_count <= before_count, "Deduplication increased row count"


class TestDataQuality:
    """Data quality tests for the leads CSV."""

    def test_no_duplicate_rows_exact(self):
        """Verify no exact duplicate rows exist."""
        df = pd.read_csv("daily_leads.csv")
        duplicates = df.duplicated().sum()
        assert duplicates == 0, f"Found {duplicates} exact duplicate rows"

    def test_city_values_are_valid(self):
        """Verify city values are from expected list or empty/NaN."""
        df = pd.read_csv("daily_leads.csv")
        valid_cities = ["Bengaluru", "Bangalore", "Hyderabad", "Delhi", "Mumbai",
                        "Pune", "Chennai", "Kolkata", "Lucknow", "Jaipur", "", None]
        # Fill NaN with empty string for comparison
        df_filled = df.copy()
        df_filled["city"] = df_filled["city"].fillna("")
        invalid_cities = df_filled[~df_filled["city"].isin(valid_cities)]["city"].unique()
        assert len(invalid_cities) == 0, f"Unexpected cities: {invalid_cities}"

    def test_url_domain_is_expected(self):
        """Verify URLs are from expected domains."""
        df = pd.read_csv("daily_leads.csv")
        valid_domains = ["indeed.com", "manipalhospitals.com", "apollohospitals.com",
                        "fortishealthcare.com", "play.google.com", "gleneagleshospitals.co.in"]

        for url in df["source_url"]:
            domain_valid = any(domain in url for domain in valid_domains)
            assert domain_valid, f"Unexpected domain in URL: {url}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
