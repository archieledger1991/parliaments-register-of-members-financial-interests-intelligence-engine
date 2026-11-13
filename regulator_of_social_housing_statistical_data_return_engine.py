import pandas as pd
import json
import os

# 1. ESTABLISH THE STATUTORY HOUSING DATASET
housing_data_json = """
[
    {
        "Registered Provider Name": "Clarion Housing Group Limited",
        "Regulatory ID": "LH4087",
        "Total Housing Stock Owned": 125000,
        "Chief Executive Salary": 384200,
        "Median Worker Wage": 29500,
        "Annual Operating Surplus": 112000000,
        "Surplus Margin %": 24.1,
        "Regulatory Scope Status": "Mandatory Large Landlord"
    },
    {
        "Registered Provider Name": "bpha Limited",
        "Regulatory ID": "LH3883",
        "Total Housing Stock Owned": 19500,
        "Chief Executive Salary": 198000,
        "Median Worker Wage": 28400,
        "Annual Operating Surplus": 34500000,
        "Surplus Margin %": 22.4,
        "Regulatory Scope Status": "Mandatory Large Landlord"
    },
    {
        "Registered Provider Name": "Amplicus Group",
        "Regulatory ID": "LH5112",
        "Total Housing Stock Owned": 14200,
        "Chief Executive Salary": 185000,
        "Median Worker Wage": 28900,
        "Annual Operating Surplus": 21800000,
        "Surplus Margin %": 19.8,
        "Regulatory Scope Status": "Mandatory Large Landlord"
    }
]
"""

# 2. THE PROCESSING ENGINE
def compile_statutory_landlord_matrix():
    print("Processing Regulatory Scope: Constructing Landlord Data Frames...")
    
    raw_df = pd.DataFrame(json.loads(housing_data_json))
    
    # Calculate the Executive-to-Worker Pay Ratio
    raw_df["Executive-to-Worker Pay Ratio"] = (raw_df["Chief Executive Salary"] / raw_df["Median Worker Wage"]).round(2)
    
    # Format currency fields neatly
    raw_df["Chief Executive Salary"] = raw_df["Chief Executive Salary"].apply(lambda x: f"£{x:,}")
    raw_df["Median Worker Wage"] = raw_df["Median Worker Wage"].apply(lambda x: f"£{x:,}")
    raw_df["Annual Operating Surplus"] = raw_df["Annual Operating Surplus"].apply(lambda x: f"£{x:,}")
    raw_df["Surplus Margin %"] = raw_df["Surplus Margin %"].apply(lambda x: f"{x}%")
    raw_df["Executive-to-Worker Pay Ratio"] = raw_df["Executive-to-Worker Pay Ratio"].apply(lambda x: f"{x}:1")
    
    ordered_matrix = raw_df[[
        "Registered Provider Name", 
        "Total Housing Stock Owned", 
        "Chief Executive Salary", 
        "Executive-to-Worker Pay Ratio",
        "Annual Operating Surplus", 
        "Surplus Margin %",
        "Regulatory Scope Status"
    ]]
    
    os.makedirs("generated", exist_ok=True)
    ordered_matrix.to_csv("generated/regulator_of_social_housing_statistical_data_return_matrix.csv", index=False)
    
    return ordered_matrix

if __name__ == "__main__":
    landlord_matrix_dataframe = compile_statutory_landlord_matrix()
    print("\n=== SYSTEMIC HOUSING DATA FRAME MATRIX PROCESSED ===")
    print(landlord_matrix_dataframe.to_string(index=False))

