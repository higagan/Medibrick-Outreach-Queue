"""
Medibrick Lead Extractor
Extracts structured recruiter-friendly fields from raw Indeed job text.
"""

import re
from datetime import datetime, timedelta


def format_date_display(date_obj):
    """Format a date as day month year, e.g. 1 june 2026."""
    month_names = [
        "", "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]
    return f"{date_obj.day} {month_names[date_obj.month]} {date_obj.year}"


def extract_hospital_name(text, source_url=""):
    """Extract hospital name from job text or source URL."""
    # Pattern: "Easily apply <HOSPITAL NAME> <City>"
    match = re.search(r'Easily apply\s+([A-Z][A-Za-z0-9\s\-&\.]+?)(?:\s+Bengaluru|\s+Bangalore|\s+Hyderabad|\s+Delhi|\s+Mumbai|\s+Pune|\s+Chennai|\s+Kolkata|\s+Lucknow|\s+Jaipur|\s+Gurgaon|\s+Noida|\s+Remote)', text)
    if match:
        return match.group(1).strip()
    
    # Fallback: look for ALL CAPS hospital names
    match = re.search(r'([A-Z][A-Z\s]+(?:HOSPITAL|CLINIC|CENTRE|CENTER|INSTITUTE|FOUNDATION|LTD|LIMITED|PVT|PRIVATE))', text)
    if match:
        return match.group(1).strip().title()
    
    # Another fallback: company name after "apply" or "hiring"
    match = re.search(r'(?:apply|hiring|by)\s+([A-Z][A-Za-z0-9\s&\.]+?)(?:\s+\d|₹|in\s|for\s|$)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # URL fallback: extract from Indeed cmp= parameter
    if source_url:
        match = re.search(r'cmp=([^&]+)', source_url)
        if match:
            name = match.group(1).replace('-', ' ').replace('_', ' ').strip()
            # Title-case and clean up
            name = ' '.join(word.capitalize() for word in name.split())
            return name
    
    return ""


def extract_role(text):
    """Extract medical role from job text."""
    roles = [
        "Duty Doctor",
        "Duty Medical Officer",
        "Resident Medical Officer",
        "Medical Officer",
        "Locum Doctor",
        "BAMS Doctor",
        "BHMS Doctor",
        "Ayurvedic Doctor",
        "Aesthetic Doctor",
        "Emergency Doctor",
        "Casualty Doctor",
        "RMO",
        "DMO",
        "Nurse",
        "Staff Nurse",
        "ICU Nurse",
        "OT Nurse",
        "Dialysis Technician",
        "Physiotherapist",
        "Radiologist",
        "Anesthesiologist",
        "Pathologist",
        "Pediatrician",
        "Gynecologist",
        "Orthopedic",
        "Cardiologist",
        "Neurologist",
        "Dermatologist",
        "ENT Specialist",
        "Ophthalmologist",
        "General Physician",
        "Junior Resident",
        "Senior Resident",
        "Consultant",
        "Specialist",
        "Medical Director",
        "Clinical Assistant",
        "Healthcare Assistant",
        "Lab Technician",
        "Pharmacist",
        "Hospital Administrator"
    ]
    
    text_lower = text.lower()
    for role in roles:
        if role.lower() in text_lower:
            return role
    
    # Fallback: generic doctor/nurse detection
    if "doctor" in text_lower:
        return "Doctor"
    if "nurse" in text_lower:
        return "Nurse"
    
    return ""


def extract_department(text):
    """Extract department/specialty from job text."""
    departments = {
        "ICU": ["icu", "intensive care"],
        "Emergency / Casualty": ["emergency", "casualty", "er ", "trauma"],
        "IVF / Fertility": ["ivf", "fertility", "reproductive"],
        "Dialysis": ["dialysis", "nephrology"],
        "Pediatrics": ["pediatric", "pediatrician", "child"],
        "Gynecology / Obstetrics": ["gynecology", "gynecologist", "obstetrics", "obgyn", "maternity"],
        "Orthopedics": ["orthopedic", "orthopaedic", "bone"],
        "Cardiology": ["cardiology", "cardiac", "heart"],
        "Neurology": ["neurology", "neuro", "brain"],
        "Dermatology": ["dermatology", "skin"],
        "ENT": ["ent", "ear nose throat", "otolaryngology"],
        "Ophthalmology": ["ophthalmology", "eye"],
        "General Medicine": ["general medicine", "internal medicine"],
        "General Surgery": ["general surgery", "surgical"],
        "Anesthesia": ["anesthesia", "anesthesiology", "anaesthesia"],
        "Radiology": ["radiology", "radiologist", "x-ray", "ultrasound"],
        "Pathology": ["pathology", "pathologist", "lab"],
        "Physiotherapy": ["physiotherapy", "physiotherapist", "rehabilitation"],
        "Ayurveda": ["ayurveda", "ayurvedic"],
        "Homeopathy": ["homeopathy", "homeopathic"],
        "Dental": ["dental", "dentistry", "dentist"],
        "Psychiatry": ["psychiatry", "psychiatrist", "mental health"],
        "Oncology": ["oncology", "cancer"],
        "Urology": ["urology", "urologist"],
        "Gastroenterology": ["gastroenterology", "gi ", "gastro"],
        "Pulmonology": ["pulmonology", "pulmonary", "chest", "respiratory"],
        "Endocrinology": ["endocrinology", "endocrine", "diabetes"],
        "Rheumatology": ["rheumatology", "rheumatologist"],
        "Nephrology": ["nephrology", "kidney"],
        "Hematology": ["hematology", "blood"],
        "Infectious Disease": ["infectious disease", "infection"],
        "Geriatrics": ["geriatrics", "geriatric", "elderly"],
        "Neonatology": ["neonatology", "neonatal", "newborn"],
        "Plastic Surgery": ["plastic surgery", "cosmetic"],
        "Neurosurgery": ["neurosurgery", "neurosurgeon"],
        "Cardiac Surgery": ["cardiac surgery", "heart surgery"],
        "Orthopedic Surgery": ["orthopedic surgery", "joint replacement"],
        "ENT Surgery": ["ent surgery", " ENT "]
    }
    
    text_lower = text.lower()
    found = []
    for dept, keywords in departments.items():
        for kw in keywords:
            if kw in text_lower:
                found.append(dept)
                break
    
    return ", ".join(found) if found else "General / Casualty"


def extract_city(text):
    """Extract city from job text."""
    cities = [
        ("Bengaluru", ["bengaluru", "bangalore"]),
        ("Hyderabad", ["hyderabad"]),
        ("Delhi", ["delhi", "new delhi"]),
        ("Mumbai", ["mumbai", "bombay"]),
        ("Pune", ["pune"]),
        ("Chennai", ["chennai", "madras"]),
        ("Kolkata", ["kolkata", "calcutta"]),
        ("Lucknow", ["lucknow"]),
        ("Jaipur", ["jaipur"]),
        ("Gurgaon", ["gurgaon", "gurugram"]),
        ("Noida", ["noida"]),
        ("Ahmedabad", ["ahmedabad"]),
        ("Chandigarh", ["chandigarh"]),
        ("Indore", ["indore"]),
        ("Bhopal", ["bhopal"]),
        ("Patna", ["patna"]),
        ("Ranchi", ["ranchi"]),
        ("Raipur", ["raipur"]),
        ("Bhubaneswar", ["bhubaneswar"]),
        ("Dehradun", ["dehradun"]),
        ("Remote", ["remote", "work from home", "wfh"])
    ]
    
    text_lower = text.lower()
    for city_name, keywords in cities:
        for kw in keywords:
            if kw in text_lower:
                return city_name
    
    return ""


def extract_salary(text):
    """Extract salary from job text."""
    # Match patterns like ₹30,000 - ₹65,000 or ₹50,000 a month
    match = re.search(r'₹[\d,]+(?:\.\d+)?(?:\s*-\s*₹[\d,]+(?:\.\d+)?)?(?:\s*(?:a month|per month|monthly|a year|annually|per year|per day|a day|per hour|an hour))?', text)
    if match:
        return match.group(0)
    return ""


def extract_hiring_type(text):
    """Extract hiring type (urgent, full-time, part-time, etc)."""
    types = []
    text_lower = text.lower()
    
    if "urgent" in text_lower or "urgently" in text_lower:
        types.append("Urgent")
    if "full-time" in text_lower or "full time" in text_lower:
        types.append("Full-time")
    if "part-time" in text_lower or "part time" in text_lower:
        types.append("Part-time")
    if "contract" in text_lower:
        types.append("Contract")
    if "temporary" in text_lower:
        types.append("Temporary")
    if "locum" in text_lower:
        types.append("Locum")
    if "flexible" in text_lower:
        types.append("Flexible")
    if "remote" in text_lower or "work from home" in text_lower:
        types.append("Remote")
    if "fresher" in text_lower or "freshers" in text_lower:
        types.append("Fresher Welcome")
    if "experienced" in text_lower:
        types.append("Experienced")
    if "immediate" in text_lower:
        types.append("Immediate Joining")
    if "night shift" in text_lower or "night duty" in text_lower:
        types.append("Night Shift")
    if "day shift" in text_lower:
        types.append("Day Shift")
    if "rotational" in text_lower:
        types.append("Rotational Shift")
    
    return ", ".join(types) if types else ""


def extract_contact_person(text):
    """Extract contact person name if mentioned."""
    # Look for patterns like "Contact: Name" or "Reach out to Name"
    match = re.search(r'(?:contact|reach out to|call|speak to|talk to)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Look for "Dr. Name" patterns
    match = re.search(r'Dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
    if match:
        return "Dr. " + match.group(1).strip()
    
    return ""


def extract_phone(text):
    """Extract phone number from text."""
    # Indian phone patterns
    patterns = [
        r'(?:\+91[-\s]?)?[6-9]\d{9}',  # Mobile
        r'(?:\+91[-\s]?)?\d{3}[-\s]?\d{8}',  # Landline with STD
        r'\d{5}[-\s]?\d{5}',  # 10-digit split
        r'(?:ph|phone|tel|contact|call)\s*[:\-]?\s*(?:\+91[-\s]?)?[6-9]\d{9}'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0)
            # Clean up
            phone = re.sub(r'[^\d+]', '', phone)
            if len(phone) == 10:
                phone = "+91 " + phone
            return phone
    
    return ""


def extract_email(text):
    """Extract email address from text."""
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if match:
        return match.group(0)
    return ""


def extract_hr_clue(text):
    """Extract HR/reception clues."""
    clues = []
    text_lower = text.lower()
    
    if "easily apply" in text_lower:
        clues.append("Apply via Indeed")
    if "walk-in" in text_lower or "walk in" in text_lower:
        clues.append("Walk-in interview")
    if "send resume" in text_lower or "send cv" in text_lower or "email cv" in text_lower:
        clues.append("Send resume/CV")
    if "call" in text_lower and any(x in text_lower for x in ["hr", "reception", "admin", "contact"]):
        clues.append("Call HR/Reception")
    if "whatsapp" in text_lower:
        clues.append("WhatsApp application")
    if "direct joining" in text_lower:
        clues.append("Direct joining possible")
    if "interview" in text_lower:
        clues.append("Interview scheduled")
    
    return "; ".join(clues) if clues else ""


def extract_notes(text):
    """Extract important notes and signals."""
    notes = []
    text_lower = text.lower()
    
    # Staffing signals
    if "urgent" in text_lower or "urgently" in text_lower:
        notes.append("Urgent requirement")
    if "immediate" in text_lower:
        notes.append("Immediate joining")
    if "fresher" in text_lower:
        notes.append("Freshers welcome")
    if "experienced" in text_lower:
        notes.append("Experienced preferred")
    if "mbbs" in text_lower:
        notes.append("MBBS required")
    if "bams" in text_lower:
        notes.append("BAMS required")
    if "bhms" in text_lower:
        notes.append("BHMS required")
    if "bds" in text_lower:
        notes.append("BDS required")
    if "gnm" in text_lower or "anm" in text_lower:
        notes.append("GNM/ANM nurses")
    if "bsc nursing" in text_lower:
        notes.append("B.Sc Nursing preferred")
    if "mci" in text_lower or "state medical council" in text_lower:
        notes.append("MCI/State Council registration required")
    if "nmc" in text_lower:
        notes.append("NMC registration required")
    if "travelling" in text_lower or "travel" in text_lower:
        notes.append("Travel may be required")
    if "accommodation" in text_lower or "stay" in text_lower or "hostel" in text_lower:
        notes.append("Accommodation provided")
    if "food" in text_lower or "meals" in text_lower:
        notes.append("Food provided")
    if "insurance" in text_lower:
        notes.append("Insurance benefits")
    if "pf" in text_lower or "provident fund" in text_lower:
        notes.append("PF benefits")
    if "esic" in text_lower:
        notes.append("ESIC coverage")
    if "bonus" in text_lower:
        notes.append("Performance bonus")
    if "incentive" in text_lower:
        notes.append("Incentives available")
    if "training" in text_lower:
        notes.append("Training provided")
    if "bond" in text_lower:
        notes.append("Service bond required")
    
    return "; ".join(notes) if notes else ""


def extract_date_posted(text, date_text=""):
    """Extract relative posting date from job text or explicit date text."""
    text_lower = text.lower()
    today = datetime.now()

    def normalize_date(days=0):
        return format_date_display(today - timedelta(days=days))

    def normalize_months(months=0):
        month = today.month - months
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        try:
            return format_date_display(today.replace(year=year, month=month))
        except:
            return normalize_date(0)
    
    # Use explicit date text if provided (from scraper HTML element)
    if date_text:
        date_lower = date_text.lower()
        # Pattern: "X days ago" or "X+ days ago"
        match = re.search(r'(\d+)\+?\s+day[s]?\s+ago', date_lower)
        if match:
            days = int(match.group(1))
            return normalize_date(days=days)
        # Pattern: "X hours ago" -> today
        if re.search(r'\d+\s+hour[s]?\s+ago', date_lower):
            return normalize_date(0)
        # Pattern: "Today"
        if "today" in date_lower:
            return normalize_date(0)
        # Pattern: "Just posted"
        if "just posted" in date_lower:
            return normalize_date(0)
        # Pattern: "Posted X days ago" or "Posted X+ days ago"
        match = re.search(r'posted\s+(\d+)\+?\s+day[s]?\s+ago', date_lower)
        if match:
            days = int(match.group(1))
            return normalize_date(days=days)
        # Pattern: "X months ago"
        match = re.search(r'(\d+)\s+month[s]?\s+ago', date_lower)
        if match:
            months = int(match.group(1))
            return normalize_months(months=months)
        return ""
    
    # Fallback: search in full text
    match = re.search(r'(\d+)\+?\s+day[s]?\s+ago', text_lower)
    if match:
        days = int(match.group(1))
        return normalize_date(days=days)
    if re.search(r'\d+\s+hour[s]?\s+ago', text_lower):
        return normalize_date(0)
    if "today" in text_lower:
        return normalize_date(0)
    if "just posted" in text_lower:
        return normalize_date(0)
    match = re.search(r'(\d+)\s+month[s]?\s+ago', text_lower)
    if match:
        months = int(match.group(1))
        return normalize_months(months=months)

    return ""


def calculate_priority(text, has_contact=False):
    """Calculate priority based on signals."""
    score = 0
    text_lower = text.lower()
    
    # Urgency signals
    if "urgent" in text_lower or "urgently" in text_lower:
        score += 3
    if "immediate" in text_lower:
        score += 2
    if "walk-in" in text_lower or "walk in" in text_lower:
        score += 2
    
    # Contact signals
    if has_contact:
        score += 2
    if "easily apply" in text_lower:
        score += 1
    
    # Salary signals (higher salary = higher priority)
    salary_match = re.search(r'₹([\d,]+)', text)
    if salary_match:
        salary_str = salary_match.group(1).replace(',', '')
        try:
            salary = int(salary_str)
            if salary >= 50000:
                score += 2
            elif salary >= 30000:
                score += 1
        except:
            pass
    
    # Role scarcity
    if "locum" in text_lower:
        score += 1
    if "duty doctor" in text_lower:
        score += 1
    if "rmo" in text_lower:
        score += 1
    
    # Convert score to priority
    if score >= 4:
        return "HIGH"
    elif score >= 2:
        return "MEDIUM"
    else:
        return "LOW"


def enrich_lead(lead_text, source_url="", date_text="", pre_hospital="", pre_city="", pre_salary="", pre_hiring_type="", pre_role=""):
    """
    Main enrichment function.
    Takes raw lead text and returns structured dictionary.
    If pre-extracted fields are provided (from structured HTML scraping),
    they are used directly; otherwise falls back to regex extraction.
    """
    text = lead_text.strip()
    
    # Use pre-extracted structured fields when available
    hospital = pre_hospital or extract_hospital_name(text, source_url)
    role = pre_role or extract_role(text)
    department = extract_department(text)
    city = pre_city or extract_city(text)
    salary = pre_salary or extract_salary(text)
    hiring_type = pre_hiring_type or extract_hiring_type(text)
    phone = extract_phone(text)
    email = extract_email(text)
    contact = extract_contact_person(text)
    hr_clue = extract_hr_clue(text)
    notes = extract_notes(text)
    
    date_posted = extract_date_posted(text, date_text=date_text)
    
    # Build contact recommendation
    if not contact and not phone and not email:
        if hospital:
            contact = "Call hospital reception/admin"
        else:
            contact = "Apply via Indeed/website"
    
    # Build notes
    all_notes = []
    if notes:
        all_notes.append(notes)
    if hr_clue:
        all_notes.append(hr_clue)
    if source_url:
        all_notes.append(f"Source: Indeed")
    
    final_notes = "; ".join(all_notes) if all_notes else "Hospital actively hiring through Indeed."
    
    return {
        "hospital": hospital,
        "role": role,
        "department": department,
        "city": city,
        "salary": salary,
        "hiring_type": hiring_type,
        "phone": phone,
        "email": email,
        "contact": contact,
        "notes": final_notes,
        "date_posted": date_posted,
        "source_url": source_url
    }


def format_lead_card(lead_dict):
    """Format enriched lead as recruiter-friendly card."""
    return f"""🏥 {lead_dict['hospital'] or 'Unknown Hospital'}
🩺 {lead_dict['role'] or 'Medical Staff'}
🏬 {lead_dict['department']}
📍 {lead_dict['city'] or 'Location not specified'}
💰 {lead_dict['salary'] or 'Not disclosed'}
⚡ {lead_dict['hiring_type'] or 'Not specified'}
📞 {lead_dict['phone'] or ''}
📧 {lead_dict['email'] or ''}
👤 {lead_dict['contact']}
📝 {lead_dict['notes']}"""


if __name__ == "__main__":
    # Test with example
    test_text = "Duty Doctor Easily apply RANGADORE MEMORIAL HOSPITAL Bengaluru, Karnataka ₹30,000 - ₹65,000 a month Full-time"
    result = enrich_lead(test_text)
    print(format_lead_card(result))
