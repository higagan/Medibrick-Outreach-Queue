import streamlit as st
import pandas as pd
import math
import os
import re
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Medibrick Outreach Queue")

# ─── CSS ─── Modern Premium SaaS Recruiter Operations Interface
st.html("""
<style>
    :root {
        --color-bg-primary: #ffffff;
        --color-bg-secondary: #f8f9fa;
        --color-bg-tertiary: #f3f5f7;
        --color-border: #e5e8eb;
        --color-border-soft: #f0f2f5;
        --color-text-primary: #0f1419;
        --color-text-secondary: #6b7280;
        --color-text-tertiary: #9ca3af;
        --color-accent: #2563eb;
        --color-success: #10b981;
        --color-warning: #f59e0b;
        --color-danger: #ef4444;
        --shadow-sm: 0 1px 2px rgba(15, 20, 25, 0.05);
        --shadow-md: 0 4px 6px rgba(15, 20, 25, 0.07);
    }

    * { box-sizing: border-box; }
    
    .block-container { 
        padding: 1.5rem 2rem !important; 
        max-width: 100% !important; 
        background: var(--color-bg-primary);
    }
    
    /* ─── HEADER ─── */
    .app-header { 
        font-size: 1.75rem; 
        font-weight: 800; 
        color: var(--color-text-primary); 
        margin-bottom: 2rem;
        letter-spacing: -0.02em;
        display: flex; 
        align-items: center; 
        gap: 0.6rem;
    }

    /* ─── METRICS CARDS ─── */
    .metrics-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 0.75rem;
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background: var(--color-bg-secondary);
        border: 1px solid var(--color-border);
        border-radius: 8px;
        padding: 1rem;
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        border-color: var(--color-accent);
        background: var(--color-bg-primary);
        box-shadow: var(--shadow-sm);
    }
    
    .metric-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--color-text-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.4rem;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--color-text-primary);
    }

    /* ─── TOOLBAR ─── */
    .toolbar-section {
        background: var(--color-bg-secondary);
        border: 1px solid var(--color-border);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 1.5rem;
    }
    
    .toolbar-label { 
        font-size: 0.65rem; 
        font-weight: 700; 
        color: var(--color-text-tertiary); 
        text-transform: uppercase; 
        letter-spacing: 0.05em; 
        margin-bottom: 0.3rem;
    }

    /* ─── TABLE HEADER ─── */
    .tbl-header-row {
        display: flex;
        align-items: center;
        gap: 0;
        padding: 0.8rem 0.6rem;
        background: var(--color-bg-secondary);
        border-bottom: 1px solid var(--color-border);
        border-radius: 6px 6px 0 0;
        margin-bottom: 0;
    }
    
    .tbl-header-cell {
        font-size: 0.75rem;
        font-weight: 800;
        color: var(--color-text-primary);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        user-select: none;
        flex: 0 0 auto;
        padding: 0.6rem 0;
        border-bottom: 2px solid var(--color-border);
    }

    /* ─── TABLE DATA ROWS ─── */
    /* Target Streamlit horizontal blocks with exactly 11 columns (table rows) */
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) {
        display: flex !important;
        align-items: center !important;
        padding: 0.9rem 0.6rem !important;
        border-bottom: 1px solid var(--color-border-soft) !important;
        transition: all 0.12s ease !important;
        background: var(--color-bg-primary) !important;
        min-height: 2.6rem !important;
        flex-wrap: nowrap !important;
    }
    
    /* Alternating row colors - use nth-of-type on the horizontal blocks */
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child):nth-of-type(odd) {
        background: var(--color-bg-primary) !important;
    }
    
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child):nth-of-type(even) {
        background: rgba(248, 249, 250, 0.5) !important;
    }
    
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child):hover {
        background: var(--color-bg-tertiary) !important;
    }
    
    /* Ensure columns don't wrap */
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn {
        flex-shrink: 0 !important;
        min-width: 0 !important;
    }

    /* Column width overrides for table rows */
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn:nth-child(1) { flex: 0 0 1.5% !important; max-width: 1.5% !important; }
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn:nth-child(2) { flex: 0 0 2.8% !important; max-width: 2.8% !important; }
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn:nth-child(3) { flex: 0 0 19% !important; max-width: 19% !important; }
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn:nth-child(4) { flex: 0 0 10% !important; max-width: 10% !important; }
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn:nth-child(5) { flex: 0 0 8% !important; max-width: 8% !important; }
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn:nth-child(6) { flex: 0 0 7.5% !important; max-width: 7.5% !important; }
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn:nth-child(7) { flex: 0 0 8.5% !important; max-width: 8.5% !important; }
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn:nth-child(8) { flex: 0 0 6.5% !important; max-width: 6.5% !important; }
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn:nth-child(9) { flex: 0 0 6.5% !important; max-width: 6.5% !important; }
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn:nth-child(10) { flex: 0 0 7.5% !important; max-width: 7.5% !important; }
    .stHorizontalBlock:has(> .stColumn:nth-child(11):last-child) > .stColumn:nth-child(11) { flex: 0 0 6.5% !important; max-width: 6.5% !important; }
    .cell-accent {
        width: 2px;
        min-width: 2px;
        height: 100%;
        border-radius: 1px;
        margin-right: 0.6rem;
    }
    
    .accent-bar { width: 3px; min-width: 3px; border-radius: 0 2px 2px 0; align-self: stretch; margin-right: 0.3rem; }
    .accent-untouched { background: #cbd5e1; }
    .accent-interested { background: #10b981; }
    .accent-followup { background: #f59e0b; }
    .accent-noresponse { background: #ef4444; }
    .accent-notinterested { background: #6b7280; }

    .cell-idx {
        font-size: 0.7rem;
        color: var(--color-text-tertiary);
        font-weight: 600;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        text-align: center;
        flex: 0 0 2.8%;
    }

    .cell-hospital {
        font-weight: 700;
        font-size: 0.85rem;
        color: var(--color-text-primary);
        line-height: 1.3;
        overflow: hidden;
        text-overflow: ellipsis;
        flex: 0 0 20%;
        min-width: 0;
    }

    .cell-hospital a {
        color: var(--color-text-primary);
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        transition: color 0.15s ease;
    }

    .cell-hospital a:hover {
        color: var(--color-accent);
    }

    .cell-hospital .link-icon {
        font-size: 0.65rem;
        color: var(--color-text-tertiary);
        opacity: 0;
        transition: opacity 0.12s ease;
    }

    .tbl-row:hover .cell-hospital .link-icon {
        opacity: 1;
    }

    .cell-updated {
        font-size: 0.65rem;
        color: var(--color-text-tertiary);
        margin-left: 0.3rem;
    }

    .cell-role {
        font-size: 0.76rem;
        color: var(--color-text-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        flex: 0 0 11%;
        min-width: 0;
    }

    .cell-dept {
        font-size: 0.75rem;
        color: var(--color-text-tertiary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        flex: 0 0 9%;
        min-width: 0;
    }

    .cell-city {
        font-size: 0.75rem;
        color: var(--color-text-secondary);
        font-weight: 500;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        flex: 0 0 8%;
        min-width: 0;
    }

    .cell-salary {
        font-size: 0.76rem;
        color: var(--color-success);
        font-weight: 700;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        flex: 0 0 9%;
        min-width: 0;
    }

    .cell-priority {
        font-size: 0.75rem;
        font-weight: 600;
        flex: 0 0 7%;
        min-width: 0;
        display: flex;
        align-items: center;
    }

    .cell-date {
        font-size: 0.75rem;
        color: var(--color-text-tertiary);
        font-weight: 500;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        flex: 0 0 6%;
        min-width: 0;
    }

    .cell-date-fresh {
        color: var(--color-success);
        font-weight: 600;
    }

    .cell-contacted {
        flex: 0 0 7%;
        min-width: 0;
    }

    .cell-response {
        flex: 0 0 8%;
        min-width: 0;
    }

    .cell-notes {
        flex: 0 0 14%;
        min-width: 0;
    }

    /* ─── CHIPS & BADGES ─── */
    .chip {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.28rem 0.6rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 700;
        line-height: 1;
        white-space: nowrap;
    }

    .chip-high { background: rgba(239, 68, 68, 0.1); color: #991b1b; }
    .chip-medium { background: rgba(245, 158, 11, 0.1); color: #92400e; }
    .chip-low { background: rgba(16, 185, 129, 0.1); color: #065f46; }

    /* ─── NOTES BUTTON ─── */
    .notes-button {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.35rem 0.6rem;
        background: var(--color-bg-secondary);
        border: 1px solid var(--color-border);
        border-radius: 5px;
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--color-text-secondary);
        cursor: pointer;
        transition: all 0.15s ease;
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
    }

    .notes-button:hover {
        background: var(--color-bg-tertiary);
        border-color: var(--color-text-secondary);
        color: var(--color-text-primary);
    }

    /* ─── BUTTONS & CONTROLS ─── */
    .stButton button {
        padding: 0.35rem 0.75rem !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        border-radius: 5px !important;
        min-height: 28px !important;
        transition: all 0.15s ease !important;
        border: none !important;
    }

    .stButton button[kind="primary"] {
        background: var(--color-accent) !important;
        color: white !important;
    }

    .stButton button[kind="secondary"] {
        background: var(--color-bg-secondary) !important;
        color: var(--color-text-secondary) !important;
        border: 1px solid var(--color-border) !important;
    }

    .stTextInput input {
        font-size: 0.75rem !important;
        padding: 0.35rem 0.6rem !important;
        border-radius: 5px !important;
        border: 1px solid var(--color-border) !important;
    }

    .stSelectbox div[data-baseweb="select"] {
        font-size: 0.75rem !important;
    }

    .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 5px !important;
        border: 1px solid var(--color-border) !important;
        background: var(--color-bg-primary) !important;
    }

    .stPopover button {
        padding: 0.35rem 0.6rem !important;
        font-size: 0.7rem !important;
        min-height: 26px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        border-radius: 5px !important;
        font-weight: 600 !important;
    }

    /* ─── FORM ELEMENTS ─── */
    .stSelectbox, .stTextInput, .stTextArea {
        margin-bottom: 0 !important;
    }

    /* ─── EMPTY STATE ─── */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: var(--color-text-tertiary);
    }

    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.6;
    }

    .empty-state-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--color-text-primary);
        margin-bottom: 0.5rem;
    }

    .empty-state-desc {
        font-size: 0.85rem;
        color: var(--color-text-tertiary);
        max-width: 400px;
        margin: 0 auto;
    }

    /* ─── PAGINATION ─── */
    .pagination-info {
        font-size: 0.75rem;
        color: var(--color-text-secondary);
        font-weight: 600;
        text-align: center;
    }

    /* ─── UTILITY ─── */
    footer { visibility: hidden; }
    header { visibility: hidden; }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] { border: none !important; padding: 0 !important; margin-bottom: 0 !important; }
    .stMarkdown { margin-bottom: 0 !important; }
</style>
""")

# ─── DATA ───

def load_data():
    if not os.path.exists("daily_leads.csv") or os.path.getsize("daily_leads.csv") == 0:
        return pd.DataFrame(columns=["hospital", "role", "department", "city", "salary", "hiring_type", "phone", "email", "contact", "notes", "date_posted", "source_url", "contacted", "response_status", "recruiter_notes", "last_updated"])
    df = pd.read_csv("daily_leads.csv", dtype=str, keep_default_na=False)
    for col, default in [("contacted", "No"), ("response_status", ""), ("recruiter_notes", "")]:
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].astype(str).replace("nan", "")
    if "date_posted" not in df.columns:
        df["date_posted"] = datetime.now().strftime("%-d %B %Y").lower()
    if "last_updated" not in df.columns:
        df["last_updated"] = ""
    # Drop legacy priority column if present
    if "priority" in df.columns:
        df = df.drop(columns=["priority"])
    return df

def save_data(df):
    df.to_csv("daily_leads.csv", index=False)

def relative_time(ts_str):
    if not ts_str or ts_str == "nan":
        return ""
    try:
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        delta = datetime.now() - dt
        if delta < timedelta(minutes=1): return "Just now"
        elif delta < timedelta(hours=1): return f"{int(delta.seconds / 60)}m ago"
        elif delta < timedelta(days=1): return f"{int(delta.seconds / 3600)}h ago"
        elif delta < timedelta(days=2): return "Yesterday"
        else: return f"{delta.days}d ago"
    except:
        return ""

def relative_date(date_str):
    if not date_str or date_str == "nan" or date_str == "":
        return "—"
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        delta = datetime.now() - dt
        if delta.days == 0: return "Today"
        elif delta.days == 1: return "1d ago"
        elif delta.days < 7: return f"{delta.days}d ago"
        elif delta.days < 14: return "1w ago"
        else: return f"{delta.days // 7}w ago"
    except:
        return date_str

def parse_date_for_sort(date_str):
    """Parse date_posted string to datetime for sorting."""
    if not date_str or date_str == "nan" or date_str == "":
        return datetime.min
    try:
        # Try new format first: "1 june 2026"
        return datetime.strptime(date_str, "%d %B %Y")
    except ValueError:
        try:
            # Fallback to old format: "2026-06-01"
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return datetime.min

def abbreviate_salary(s):
    if not s or s == "—":
        return "—"
    basis = ""
    s_lower = s.lower()
    if "hour" in s_lower or "hr" in s_lower:
        basis = "/hr"
    elif "day" in s_lower:
        basis = "/day"
    elif "week" in s_lower:
        basis = "/wk"
    elif "month" in s_lower:
        basis = "/mo"
    elif "year" in s_lower or "annum" in s_lower:
        basis = "/yr"

    nums = re.findall(r"[\d,]+", s)
    if not nums:
        return s
    vals = [int(n.replace(",", "")) for n in nums]
    val = vals[0] if len(vals) == 1 else sum(vals) // len(vals)

    if val >= 100000:
        formatted = f"₹{val//100000}L"
    elif val >= 1000:
        if val < 10000 and basis in ("/day", "/hr"):
            formatted = f"₹{val/1000:.1f}K"
        else:
            formatted = f"₹{val//1000}K"
    else:
        formatted = f"₹{val}"
    return f"{formatted}{basis}"

def extract_phone(text):
    phones = re.findall(r'(?:\+91[-\s]?)?[6-9]\d{9}', text)
    return phones[0] if phones else None

def extract_email(text):
    emails = re.findall(r'[\w.-]+@[\w.-]+\.\w+', text)
    return emails[0] if emails else None

df = load_data()

# ─── HEADER ───
st.html("<div class='app-header'>🏥 Medibrick Outreach Queue</div>")

# ─── METRICS CARDS ───
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.html(f"""
    <div class='metric-card'>
        <div class='metric-label'>Total Leads</div>
        <div class='metric-value'>{len(df)}</div>
    </div>
    """)

with col2:
    not_contacted = len(df[df["contacted"] == "No"])
    st.html(f"""
    <div class='metric-card'>
        <div class='metric-label'>Not Contacted</div>
        <div class='metric-value'>{not_contacted}</div>
    </div>
    """)

with col3:
    interested = len(df[df["response_status"] == "Interested"])
    st.html(f"""
    <div class='metric-card'>
        <div class='metric-label'>Interested</div>
        <div class='metric-value'>{interested}</div>
    </div>
    """)

with col4:
    followup = len(df[df["response_status"] == "Follow-up Needed"])
    st.html(f"""
    <div class='metric-card'>
        <div class='metric-label'>Follow-up</div>
        <div class='metric-value'>{followup}</div>
    </div>
    """)

with col5:
    no_response = len(df[df["response_status"] == "No Response"])
    st.html(f"""
    <div class='metric-card'>
        <div class='metric-label'>No Response</div>
        <div class='metric-value'>{no_response}</div>
    </div>
    """)

# Apply quick filter
filtered = df.copy()

# ─── TOOLBAR ───
cities = ["All"] + sorted(df["city"].replace("", pd.NA).dropna().unique().tolist())
status_opts = ["All"] + sorted(df["contacted"].replace("", pd.NA).dropna().unique().tolist())
response_opts = ["All"] + sorted([x for x in df["response_status"].replace("", pd.NA).dropna().unique().tolist() if x])

tb = st.columns([2.4, 1.0, 1.0, 1.0, 1.0, 0.6, 0.4])
with tb[0]:
    st.html("<div class='toolbar-label'>Search</div>")
    search = st.text_input("Search", placeholder="Hospital, role, city...", label_visibility="collapsed", key="search")
with tb[1]:
    st.html("<div class='toolbar-label'>City</div>")
    city_filter = st.selectbox("City", cities, index=0, label_visibility="collapsed", key="city")
with tb[2]:
    st.html("<div class='toolbar-label'>Status</div>")
    status_filter = st.selectbox("Status", status_opts, index=0, label_visibility="collapsed", key="status")
with tb[3]:
    st.html("<div class='toolbar-label'>Response</div>")
    response_filter = st.selectbox("Response", response_opts, index=0, label_visibility="collapsed", key="response")
with tb[4]:
    st.html("<div class='toolbar-label'>Sort</div>")
    sort_by = st.selectbox("Sort", ["Date ↓", "Date ↑", "Salary ↓", "Salary ↑"], index=0, label_visibility="collapsed", key="sort")
with tb[5]:
    st.html("<div class='toolbar-label'>&nbsp;</div>")
    if st.button("➕", key="add_lead_btn", use_container_width=True, help="Add new lead"):
        st.session_state.show_add_lead = True
with tb[6]:
    st.html("<div class='toolbar-label'>&nbsp;</div>")
    if st.button("↻", key="refresh", help="Refresh data"):
        st.rerun()

# Apply filters
if search:
    filtered = filtered[filtered.astype(str).apply(lambda r: r.str.contains(search, case=False).any(), axis=1)]
if city_filter != "All":
    filtered = filtered[filtered["city"] == city_filter]
if status_filter != "All":
    filtered = filtered[filtered["contacted"] == status_filter]
if response_filter != "All":
    filtered = filtered[filtered["response_status"] == response_filter]

# Sort
def salary_num(s):
    nums = re.findall(r"[\d,]+", str(s))
    return max((int(n.replace(",", "")) for n in nums), default=0) if nums else 0

if sort_by == "Date ↓":
    filtered = filtered.assign(__d=filtered["date_posted"].apply(parse_date_for_sort)).sort_values("__d", ascending=False).drop("__d", axis=1)
elif sort_by == "Date ↑":
    filtered = filtered.assign(__d=filtered["date_posted"].apply(parse_date_for_sort)).sort_values("__d", ascending=True).drop("__d", axis=1)
elif sort_by == "Salary ↓":
    filtered = filtered.assign(__s=filtered["salary"].apply(salary_num)).sort_values("__s", ascending=False).drop("__s", axis=1)
elif sort_by == "Salary ↑":
    filtered = filtered.assign(__s=filtered["salary"].apply(salary_num)).sort_values("__s", ascending=True).drop("__s", axis=1)

# ─── ADD LEAD FORM ───
if st.session_state.get("show_add_lead", False):
    with st.form("add_lead_form"):
        st.subheader("➕ Add New Lead")
        c1, c2, c3 = st.columns(3)
        with c1:
            new_hospital = st.text_input("Hospital *", placeholder="Apollo Hospital")
        with c2:
            new_role = st.text_input("Role *", placeholder="Duty Doctor")
        with c3:
            new_dept = st.text_input("Department", placeholder="General / Casualty")
        c4, c5, c6 = st.columns(3)
        with c4:
            new_city = st.text_input("City *", placeholder="Bengaluru")
        with c5:
            new_salary = st.text_input("Salary", placeholder="₹50,000 a month")
        with c6:
            new_url = st.text_input("Source URL", placeholder="https://indeed.com/...")
        new_notes = st.text_area("Notes", placeholder="HR contact, phone, requirements...", height=60)
        submitted = st.form_submit_button("💾 Save Lead")
        cancelled = st.form_submit_button("Cancel")
        if submitted and new_hospital and new_role and new_city:
            new_row = {
                "hospital": new_hospital, "role": new_role, "department": new_dept,
                "city": new_city, "salary": new_salary,
                "contacted": "No", "response_status": "", "recruiter_notes": new_notes,
                "source_url": new_url, "date_posted": datetime.now().strftime("%-d %B %Y").lower(),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            for col in df.columns:
                if col not in new_row: new_row[col] = ""
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.toast("Lead added", icon="✅")
            st.session_state.show_add_lead = False
            st.rerun()
        if cancelled:
            st.session_state.show_add_lead = False
            st.rerun()

# ─── PAGINATION STATE ───
ROWS_PER_PAGE = 14
total_pages = math.ceil(len(filtered) / ROWS_PER_PAGE)
if total_pages < 1: total_pages = 1

if "page_num" not in st.session_state:
    st.session_state.page_num = 1

# Reset to page 1 when filters change
if st.session_state.get("_last_filter_hash") != hash((search, city_filter, status_filter, response_filter, sort_by)):
    st.session_state.page_num = 1
    st.session_state._last_filter_hash = hash((search, city_filter, status_filter, response_filter, sort_by))

if st.session_state.page_num > total_pages:
    st.session_state.page_num = total_pages
if st.session_state.page_num < 1:
    st.session_state.page_num = 1

page = st.session_state.page_num
start = (page - 1) * ROWS_PER_PAGE
end = start + ROWS_PER_PAGE
page_df = filtered.iloc[start:end]

# ─── TABLE HEADER ───
header_labels = ["", "#", "Hospital", "Role", "Department", "City", "Salary", "Posted", "Contacted", "Response", "Notes"]
header_ratios = [0.015, 0.028, 0.19, 0.10, 0.08, 0.075, 0.085, 0.065, 0.065, 0.075, 0.065]

header_cols = st.columns(header_ratios)
for col, label in zip(header_cols, header_labels):
    with col:
        st.html(f'<div class="tbl-header-cell">{label}</div>')

# ─── TABLE ROWS ───
if len(page_df) == 0:
    st.html("""
    <div class="empty-state">
        <div class="empty-state-icon">🔍</div>
        <div class="empty-state-title">No leads match your filters</div>
        <div class="empty-state-desc">Try adjusting your search, city, or status filters to see more results.</div>
    </div>
    """)
else:
    for idx, row in page_df.iterrows():
        original_idx = idx
        is_last = idx == page_df.index[-1]
        row_num = start + list(page_df.index).index(idx) + 1

        response = row.get("response_status", "")
        contacted = row.get("contacted", "No")

        if response == "Interested": accent_class = "accent-interested"
        elif response == "Follow-up Needed": accent_class = "accent-followup"
        elif response == "No Response": accent_class = "accent-noresponse"
        elif response == "Not Interested": accent_class = "accent-notinterested"
        else: accent_class = "accent-untouched"

        hospital = row.get("hospital", "").strip() or "Unknown Hospital"
        source_url = row.get("source_url", "").strip()
        updated = relative_time(row.get("last_updated", ""))
        updated_html = f'<span class="cell-updated">({updated})</span>' if updated else ""
        role = row.get("role", "").strip() or "—"
        dept = row.get("department", "").strip() or "—"
        city = row.get("city", "").strip() or "—"
        salary = abbreviate_salary(row.get("salary", "").strip())
        date_posted = relative_date(row.get("date_posted", ""))
        date_fresh = "cell-date-fresh" if date_posted == "Today" else ""

        ca, c0, c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns(header_ratios)

        with ca:
            st.html(f'<div class="accent-bar {accent_class}"></div>')

        with c0:
            st.html(f'<div class="cell-idx">{row_num}</div>')

        with c1:
            st.html(f"<div class='cell-hospital'><a href='{source_url}' target='_blank'>{hospital}<span class='link-icon'>↗</span></a>{updated_html}</div>")

        with c2:
            st.html(f"<div class='cell-role'>{role}</div>")

        with c3:
            st.html(f"<div class='cell-dept'>{dept}</div>")

        with c4:
            st.html(f"<div class='cell-city'>{city}</div>")

        with c5:
            st.html(f"<div class='cell-salary'>{salary}</div>")

        with c6:
            st.html(f"<div class='cell-date {date_fresh}'>{date_posted}</div>")

        with c7:
            cur_c = row.get("contacted", "No")
            new_c = st.selectbox("Contacted", ["No", "Yes"], index=0 if cur_c == "No" else 1, key=f"c_{original_idx}", label_visibility="collapsed")
            if new_c != cur_c:
                df.loc[original_idx, "contacted"] = new_c
                df.loc[original_idx, "last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_data(df)
                st.toast("Updated", icon="✅")
                st.rerun()

        with c8:
            cur_r = row.get("response_status", "")
            opts_r = ["", "Interested", "Follow-up", "No Response", "Not Interested"]
            idx_r = opts_r.index(cur_r) if cur_r in opts_r else 0
            new_r = st.selectbox("Response", opts_r, index=idx_r, key=f"r_{original_idx}", label_visibility="collapsed")
            if new_r != cur_r:
                df.loc[original_idx, "response_status"] = new_r
                df.loc[original_idx, "last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_data(df)
                st.toast("Updated", icon="✅")
                st.rerun()

        with c9:
            notes = str(row.get("recruiter_notes", "")).replace("nan", "")
            has_notes = bool(notes.strip())
            preview = notes[:24] + "…" if len(notes) > 24 else notes if has_notes else ""
            popover_label = f"📝 {preview}" if preview else "📝"
            
            with st.popover(popover_label, use_container_width=False):
                st.markdown(f"### {hospital}")
                new_n = st.text_area("Notes", value=notes, placeholder="HR contact, requirements, call times...", height=100, key=f"np_{original_idx}")
                
                phone = extract_phone(new_n if new_n else notes)
                email = extract_email(new_n if new_n else notes)
                
                if phone or email:
                    st.markdown("---")
                    if phone:
                        st.code(phone, language=None)
                        if st.button("📋 Copy Phone", key=f"cp_{original_idx}", use_container_width=True):
                            st.toast(f"Copied {phone}", icon="📋")
                    if email:
                        st.code(email, language=None)
                        if st.button("📋 Copy Email", key=f"ce_{original_idx}", use_container_width=True):
                            st.toast(f"Copied {email}", icon="📋")
                
                if st.button("💾 Save Notes", key=f"ns_{original_idx}", use_container_width=True, type="primary"):
                    df.loc[original_idx, "recruiter_notes"] = new_n
                    df.loc[original_idx, "last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_data(df)
                    st.toast("Notes saved", icon="✅")
                    st.rerun()

        if not is_last:
            st.html("<hr style='margin:0.1rem 0; border-color:var(--color-border-soft);'>")

# ─── BOTTOM PAGINATION ───
if len(filtered) > 0:
    st.markdown("")  # spacing
    pag_col1, pag_col2 = st.columns([1, 0.2])
    with pag_col2:
        c_prev, c_info, c_next = st.columns([0.6, 1.0, 0.6], gap="small")
        with c_prev:
            if st.button("←", key="bot_prev", disabled=page <= 1, use_container_width=True):
                st.session_state.page_num -= 1
                st.rerun()
        with c_info:
            st.html(f'<div class="pagination-info">{start+1}–{min(end, len(filtered))} of {len(filtered)}</div>')
        with c_next:
            if st.button("→", key="bot_next", disabled=page >= total_pages, use_container_width=True):
                st.session_state.page_num += 1
                st.rerun()

# ─── EXPORT ───
st.markdown("")  # spacing
today_str = datetime.now().strftime("%Y%m%d")
csv_data = df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Export CSV", csv_data, f"medibrick_{today_str}.csv", "text/csv", use_container_width=False)
