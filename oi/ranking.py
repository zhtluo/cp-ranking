import os
import re
import numpy as np
import pandas as pd
from scipy.stats import kendalltau


# Function to load data and process it into a dataframe
def load_data(file_path):
    data = []
    with open(file_path, "r", encoding="utf-8") as infile:
        for line in infile:
            parts = line.strip().split(",")
            if len(parts) >= 8:
                contest, award, name, grade, school, score, province, _, identifier = (
                    parts
                )
                identifier = identifier.strip() if identifier else ""
                # Extract only the numeric part of the score (before parentheses)
                score_match = re.match(r"([\d.]+)", score)
                score = float(score_match.group(1)) if score_match else None
                data.append((name, identifier, score))
    df = pd.DataFrame(data, columns=["Name", "Identifier", "Score"])
    return df


# Function to calculate ranks
def calculate_rank(key, df, score_column):
    df[f"Rank_{key}"] = df[score_column].rank(method="min", ascending=False)
    return df


# Merge data to find students in both contests
def merge_data(data1, data2, contest1, contest2):
    # Remove duplicate rows before merging
    data1 = data1.drop_duplicates(subset=["Name", "Identifier"])
    data2 = data2.drop_duplicates(subset=["Name", "Identifier"])

    # Perform the merge
    merged_data = pd.merge(
        data1,
        data2,
        on=["Name", "Identifier"],
        suffixes=(f"_{contest1}", f"_{contest2}"),
    )
    return merged_data


# Function to compare contests across multiple years
def compare_contests_across_years(start_year, end_year, data_dir="data"):
    results = []

    for year in range(start_year, end_year + 1):
        noip_file = f"{data_dir}/NOIP{year}.csv"
        noi_file = f"{data_dir}/NOI{year}.csv"
        ioi_file = f"{data_dir}/IOI{year + 1}.csv"  # IOI happens one year later

        # Check if files exist
        if not (
            os.path.exists(noip_file)
            and os.path.exists(noi_file)
            and os.path.exists(ioi_file)
        ):
            print(f"Skipping year {year} due to missing files.")
            continue

        try:
            # Load data
            noip_data = load_data(noip_file)
            noi_data = load_data(noi_file)
            ioi_data = load_data(ioi_file)

            # NOI vs NOIP
            merged_noi_noip = merge_data(noi_data, noip_data, "NOI", "NOIP")
            merged_noi_noip = calculate_rank("NOI", merged_noi_noip, "Score_NOI")
            merged_noi_noip = calculate_rank("NOIP", merged_noi_noip, "Score_NOIP")
            tau_noi_noip, p_noi_noip = kendalltau(
                merged_noi_noip["Rank_NOI"], merged_noi_noip["Rank_NOIP"]
            )

            # NOI vs IOI
            merged_noi_ioi = merge_data(noi_data, ioi_data, "NOI", "IOI")
            merged_noi_ioi = calculate_rank("NOI", merged_noi_ioi, "Score_NOI")
            merged_noi_ioi = calculate_rank("IOI", merged_noi_ioi, "Score_IOI")
            tau_noi_ioi, p_noi_ioi = kendalltau(
                merged_noi_ioi["Rank_NOI"], merged_noi_ioi["Rank_IOI"]
            )

            # Store results
            results.append(
                {
                    "Year": year,
                    "NOI_NOIP_Common": len(merged_noi_noip),
                    "NOI_NOIP_Tau": tau_noi_noip,
                    "NOI_NOIP_P": p_noi_noip,
                    "NOI_IOI_Common": len(merged_noi_ioi),
                    "NOI_IOI_Tau": tau_noi_ioi,
                    "NOI_IOI_P": p_noi_ioi,
                }
            )

        except Exception as e:
            print(f"Error processing year {year}: {e}")

    # Convert results to a DataFrame and display
    results_df = pd.DataFrame(results)
    if not results_df.empty:
        print(results_df)
        results_df.to_csv(f"{data_dir}/contest_comparison_results.csv", index=False)
    else:
        print("No results to display. Ensure data files are available.")


# Run the comparison
if __name__ == "__main__":
    compare_contests_across_years(2008, 2023)
