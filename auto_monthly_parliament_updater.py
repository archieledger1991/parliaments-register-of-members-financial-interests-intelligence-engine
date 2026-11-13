
import requests
import pandas as pd
import base64
import time
from datetime import datetime

def run_monthly_parliament_refresh():
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"[{timestamp}] Starting automated monthly UK Parliament data refresh...")
    
    base_url = base64.b64decode("aHR0cHM6Ly9pbnRlcmVzdHMtYXBpLnBhcmxpYW1lbnQudWsvYXBpL3Yy").decode("utf-8")
    categories_url = f"{base_url}/Categories"
    interests_url = f"{base_url}/Interests"
    headers = {"Accept": "application/json"}
    
    # 1. IDENTIFY LANDLORD & GIFT CATEGORIES
    landlord_cat_ids = []
    gift_cat_ids = []
    
    cat_res = requests.get(categories_url, headers=headers, timeout=20)
    for cat in cat_res.json().get("items", []):
        c_id = cat.get("id")
        c_name = cat.get("name", "")
        if "land" in c_name.lower() or "property" in c_name.lower():
            landlord_cat_ids.append((c_id, c_name))
        elif any(w in c_name.lower() for w in ["gift", "hospitality", "donation"]):
            gift_cat_ids.append((c_id, c_name))
            
    # 2. EXTRACT ALL VERIFIED MP LANDLORDS
    landlord_records = []
    for cat_id, cat_name in landlord_cat_ids:
        skip = 0
        while True:
            res = requests.get(interests_url, params={"CategoryId": cat_id, "Take": 50, "Skip": skip}, headers=headers, timeout=30)
            items = res.json().get("items", [])
            if not items:
                break
            for item in items:
                member = item.get("registrant", {}).get("memberDetail") or {}
                versions = item.get("versions") or []
                latest = versions[0] if versions else {}
                landlord_records.append({
                    "MP Name": member.get("nameDisplayAs", "Unknown MP"),
                    "Party": member.get("party", "Independent"),
                    "Constituency": member.get("memberFrom", "UK Parliament"),
                    "Category": cat_name,
                    "Property & Rental Disclosure": latest.get("summary", "Property asset declared"),
                    "Date Registered": latest.get("registrationDate", "Unknown")
                })
            skip += 50
            time.sleep(0.4)
            
    landlords_df = pd.DataFrame(landlord_records)
    landlords_df.to_csv("verified_mp_landlords_register.csv", index=False, encoding="utf-8")
    
    with open("READABLE_MP_LANDLORD_BRIEFING.md", "w", encoding="utf-8") as f:
        f.write("# INVESTIGATIVE BRIEFING: VERIFIED PARLIAMENTARY LANDLORDS & PROPERTY OWNERS\n")
        f.write(f"**Last Automated Update:** {timestamp} | **Total Verified Disclosures:** {len(landlords_df)}\n\n---\n\n")
        for _, row in landlords_df.iterrows():
            f.write(f"### {row['MP Name']} ({row['Party']} — {row['Constituency']})\n")
            f.write(f"* **Category:** {row['Category']}\n")
            f.write(f"* **Property & Rental Disclosure:** {row['Property & Rental Disclosure']}\n")
            f.write(f"* **Date Registered:** {row['Date Registered']}\n\n")
            
    # 3. CROSS-REFERENCE LANDLORD MPs AGAINST GIFTS & HOSPITALITY
    landlord_names = set(landlords_df["MP Name"].dropna().unique())
    gift_records = []
    
    for cat_id, cat_name in gift_cat_ids:
        skip = 0
        while skip < 600:
            res = requests.get(interests_url, params={"CategoryId": cat_id, "Take": 50, "Skip": skip}, headers=headers, timeout=30)
            items = res.json().get("items", [])
            if not items:
                break
            for item in items:
                member = item.get("registrant", {}).get("memberDetail") or {}
                mp_name = member.get("nameDisplayAs", "Unknown MP")
                if mp_name in landlord_names:
                    versions = item.get("versions") or []
                    latest = versions[0] if versions else {}
                    summary = latest.get("summary", "Gift/Benefit declared")
                    prop_keywords = ["property", "housing", "developer", "estate", "construction", "homes", "build", "clarion", "bpha", "amplicus"]
                    is_flagged = any(k in summary.lower() for k in prop_keywords)
                    
                    gift_records.append({
                        "MP Name": mp_name,
                        "Party": member.get("party", "Independent"),
                        "Constituency": member.get("memberFrom", "UK Parliament"),
                        "Is Verified Landlord?": "YES — LANDLORD MP",
                        "Conflict Flag": "FLAGGED PROPERTY CONFLICT" if is_flagged else "General Gift/Donation",
                        "Category": cat_name,
                        "Gift / Donor Details": summary,
                        "Date Registered": latest.get("registrationDate", "Unknown")
                    })
            skip += 50
            time.sleep(0.4)
            
    overlap_df = pd.DataFrame(gift_records)
    overlap_df.to_csv("nexus_landlord_mps_receiving_gifts.csv", index=False, encoding="utf-8")
    
    with open("READABLE_LANDLORD_MP_GIFTS_NEXUS.md", "w", encoding="utf-8") as f:
        f.write("# INVESTIGATIVE NEXUS BRIEFING: CONFLICTS OF INTEREST & LANDLORD MPs\n")
        f.write(f"**Last Automated Update:** {timestamp} | **Total Overlapping Disclosures:** {len(overlap_df)}\n\n---\n\n")
        for _, row in overlap_df.iterrows():
            badge = "🚨 **[FLAGGED PROPERTY CONFLICT]** " if row["Conflict Flag"] == "FLAGGED PROPERTY CONFLICT" else ""
            f.write(f"### {badge}{row['MP Name']} ({row['Party']} — {row['Constituency']})\n")
            f.write(f"* **Register Category:** {row['Category']}\n")
            f.write(f"* **Gift / Donor Details:** {row['Gift / Donor Details']}\n")
            f.write(f"* **Date Registered:** {row['Date Registered']}\n\n")
            
    print(f"[{timestamp}] Automated refresh complete! Updated {len(landlords_df)} landlords and {len(overlap_df)} overlaps.")

if __name__ == "__main__":
    run_monthly_parliament_refresh()
