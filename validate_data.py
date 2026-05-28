"""
Data validation script - run after scraping to check data quality.
This is NOT a pytest test - it's a validation report for today's scrape.
Usage: python validate_data.py
"""

import pandas as pd
import sys


def validate_csv(filepath="daily_leads.csv"):
    """Validate the scraped data and print a report."""
    print("=" * 60)
    print("DAILY LEADS VALIDATION REPORT")
    print("=" * 60)

    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"❌ ERROR: {filepath} not found. Run scraper first.")
        return False

    issues = []
    warnings = []

    # Check 1: Required columns
    required = ["city", "salary", "lead_text", "source_url"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        issues.append(f"Missing columns: {missing}")
    else:
        print(f"✅ All required columns present")

    # Check 2: No empty source URLs
    empty_urls = df["source_url"].isna() | (df["source_url"] == "")
    if empty_urls.any():
        issues.append(f"Empty source URLs: {empty_urls.sum()} rows")
    else:
        print(f"✅ No empty source URLs")

    # Check 3: No placeholder URLs
    placeholder_patterns = ["fedcba9876543210", "abcdef0123456789", "890abcdef0123456"]
    placeholder_count = 0
    for pattern in placeholder_patterns:
        matches = df["source_url"].str.contains(pattern, na=False)
        placeholder_count += matches.sum()
    if placeholder_count > 0:
        issues.append(f"Placeholder URLs found: {placeholder_count}")
    else:
        print(f"✅ No placeholder URLs")

    # Check 4: URLs are absolute
    non_http = ~df["source_url"].str.startswith("http", na=False)
    if non_http.any():
        issues.append(f"Non-HTTP URLs: {non_http.sum()}")
    else:
        print(f"✅ All URLs are absolute")

    # Check 5: Lead text not empty
    empty_text = df["lead_text"].isna() | (df["lead_text"] == "")
    if empty_text.any():
        issues.append(f"Empty lead text: {empty_text.sum()} rows")
    else:
        print(f"✅ All lead text present")

    # Check 6: Reasonable row count
    row_count = len(df)
    if row_count == 0:
        issues.append("No leads found!")
    elif row_count < 10:
        warnings.append(f"Only {row_count} leads found (expected more)")
    else:
        print(f"✅ {row_count} leads found")

    # Check 7: Salary format (warning only)
    non_empty_salary = df[df["salary"].notna() & (df["salary"] != "")]
    if len(non_empty_salary) > 0:
        has_rupee = non_empty_salary["salary"].str.contains("₹", na=False)
        if not has_rupee.all():
            warnings.append(f"Some salaries missing ₹ symbol: {(~has_rupee).sum()}")

    # Check 8: City values
    valid_cities = ["Bengaluru", "Bangalore", "Hyderabad", "Delhi", "Mumbai",
                    "Pune", "Chennai", "Kolkata", "Lucknow", "Jaipur", ""]
    df_filled = df.copy()
    df_filled["city"] = df_filled["city"].fillna("")
    invalid_cities = df_filled[~df_filled["city"].isin(valid_cities)]["city"].unique()
    if len(invalid_cities) > 0:
        warnings.append(f"Unexpected cities: {list(invalid_cities)}")

    print("-" * 60)
    if issues:
        print(f"❌ {len(issues)} ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
        print("-" * 60)
        return False
    else:
        print("✅ ALL CHECKS PASSED")

    if warnings:
        print(f"⚠️  {len(warnings)} WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")

    print("=" * 60)
    return True


if __name__ == "__main__":
    success = validate_csv()
    sys.exit(0 if success else 1)
