#!/bin/bash

echo "================================"
echo "MEDIBRICK DAILY UPDATE"
echo "================================"

# Move to project directory

cd /Users/gagandeep/medibrick-leads

# Activate virtual environment

source venv/bin/activate

# Run scraper

echo "Running scraper..."
python scraper.py

# Check scraper success

if [ $? -ne 0 ]; then
echo "Scraper failed!"
exit 1
fi

# Commit and push updated CSV

echo "Pushing latest leads..."

git add daily_leads.csv
git commit -m "Daily leads update $(date '+%Y-%m-%d %H:%M')"
git push

echo ""
echo "================================"
echo "DONE"
echo "CSV pushed to GitHub"
echo "Streamlit will refresh automatically"
echo "================================"
