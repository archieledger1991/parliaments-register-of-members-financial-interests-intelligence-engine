import requests
import pandas as pd
import base64
import time
import os

def run_landlord_and_gifts_nexus_scanner():
    print("Initializing Conflicts of Interest Engine: Matching Landlord MPs against Category 3 Gifts & Hospitality...")
    
    base_url = base64.b64decode("aHR0cHM6Ly9pbnRlcmVzdHMtYXBpLnBhcmxpYW1lbnQudWsvYXBpL3Yy").decode("utf-8")
    categories_url = f"{base_url}/Categories"
    interests_url = f"{base_url}/Interests"
    headers = {"Accept": "application/json"}
    
    landlord_csv = "generated/verified_mp_landlords_register.csv"
    if os.path.exists(landlord_csv):
        landlords_df = pd.read_csv(landlord_csv)
    else:
        landlords_df = pd.DataFrame()
        
    landlord_names = set(landlords_df["MP Name"].dropna().unique()) if not landlords_df.empty else set()
    print(f"Loaded {len(landlord_names)} unique Landlord MPs to cross-examine.\n")
    
    target_cat_ids = []
    try:
        cat_res = requests.get(categories_url, headers=headers, timeout=15)
        for cat in cat_res.json().get("items", []):
            cat_name = cat.get("name", "")
            if any(word in cat_name.lower() for word in ["gift", "hospitality", "donation"]):
                target_cat_ids.append((cat.get("id"), cat_name))
    except Exception as e:
        print(f"Category lookup note: {e}")

    gift_records = []
    
    for cat_id, cat_name in target_cat_ids:
        skip = 0
        batch_size = 50
        while skip < 500:
            res = requests.get(
                interests_url,
                params={"CategoryId": cat_id, "Take": batch_size, "Skip": skip},
                headers=headers,
                timeout=30
            )
            items = res.json().get("items", [])
            if not items:
                break
                
            for item in items:
                registrant = item.get("registrant", {})
                member_detail = registrant.get("memberDetail") or {}
                
                mp_name = member_detail.get("nameDisplayAs", "Unknown MP")
                party = member_detail.get("party", "Independent")
                constituency = member_detail.get("memberFrom", "UK Parliament")
                
                versions = item.get("versions") or []
                latest_version = versions[0] if versions else {}
                clean_summary = latest_version.get("summary", "Gift/Benefit declared")
                reg_date = latest_version.get("registrationDate", "Unknown")
                
                is_also_landlord = mp_name in landlord_names
                
                gift_records.append({
                    "MP Name": mp_name,
                    "Party": party,
                    "Constituency": constituency,
                    "Is Verified Landlord?": "YES — LANDLORD MP" if is_also_landlord else "No",
                    "Category": cat_name,
                    "Gift / Donor Details": clean_summary,
                    "Date Registered": reg_date
                })
                
            skip += batch_size
            time.sleep(0.5)

    gifts_df = pd.DataFrame(gift_records)
    overlap_df = gifts_df[gifts_df["Is Verified Landlord?"] == "YES — LANDLORD MP"].copy()
    
    prop_keywords = ["property", "housing", "developer", "estate", "construction", "homes", "build", "clarion", "bpha", "amplicus"]
    pattern = "|".join(prop_keywords)
    overlap_df["Conflict of Interest Flag"] = overlap_df["Gift / Donor Details"].str.contains(pattern, case=False, na=False).map({True: "FLAGGED PROPERTY CONFLICT", False: "General Gift/Donation"})
    
    os.makedirs("generated", exist_ok=True)
    csv_path = "generated/nexus_landlord_mps_receiving_gifts.csv"
    overlap_df.to_csv(csv_path, index=False, encoding="utf-8")
    
    md_path = "generated/READABLE_LANDLORD_MP_GIFTS_NEXUS.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# INVESTIGATIVE NEXUS BRIEFING: CONFLICTS OF INTEREST & LANDLORD MPs\n")
        f.write("**Source:** UK Parliament Register of Members' Financial Interests (Cross-Referenced Categories)\n")
        f.write(f"**Total Overlapping Disclosures Found:** {len(overlap_df)}\n\n")
        f.write("---\n\n")
        
        for _, row in overlap_df.iterrows():
            flag_badge = "🚨 **[FLAGGED PROPERTY CONFLICT]** " if row["Conflict of Interest Flag"] == "FLAGGED PROPERTY CONFLICT" else ""
            f.write(f"### {flag_badge}{row['MP Name']} ({row['Party']} — {row['Constituency']})\n")
            f.write(f"* **Status:** {row['Is Verified Landlord?']}\n")
            f.write(f"* **Register Category:** {row['Category']}\n")
            f.write(f"* **Gift / Donor Details:** {row['Gift / Donor Details']}\n")
            f.write(f"* **Date Registered:** {row['Date Registered']}\n\n")
            
    print(f"=== CONFLICTS OF INTEREST SCAN COMPLETE ===")
    print(f"Overlapping disclosures involving Verified Landlord MPs: {len(overlap_df)}")

if __name__ == "__main__":
    run_landlord_and_gifts_nexus_scanner()

