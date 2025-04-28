import yaml
import requests
import os

SKIP_PREV_GENERATED = True

# Load the YAML file with contest IDs
def load_contest_ids(file_path):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


# Fetch ranking data for a specific contest ID
def fetch_ranking(contest_id, output_dir, contest_name, year):
    yaml_filename = f"{contest_name}_{year}_ranking.yaml"
    yaml_output_path = os.path.join(output_dir, yaml_filename)

    if SKIP_PREV_GENERATED and os.path.exists(yaml_output_path):
        print(f"  [SKIP] {yaml_filename} already exists – not re-downloading.")
        return

    url = f"https://icpc.global/api/contest/public/search/contest/{contest_id}?q=proj:rank,institution,teamName,problemsSolved,totalTime,lastProblemTime,medalCitation%3B&page=1&size=1000"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Convert and save the data to YAML
        with open(yaml_output_path, "w") as yaml_file:
            yaml.dump(data, yaml_file, default_flow_style=False)
        print(f"--Saved ranking data in YAML for "\
              f"{contest_name} {year} to {yaml_output_path}")

    except requests.RequestException as e:
        print(f"[WARN] Failed to fetch ranking for contest ID {contest_id}: {e}")


# Main script
if __name__ == "__main__":
    # Load contest IDs from the YAML file
    contest_ids_file = "./outputs/contest_ids.yaml"
    contest_ids = load_contest_ids(contest_ids_file)

    # Specify the output directory
    output_dir = "./outputs/rankings"
    os.makedirs(output_dir, exist_ok=True)

    # Fetch rankings for all contests
    for contest_name, years in contest_ids.items():
        for year, contest_id in years.items():
            print(f"Fetching ranking for {contest_name} {year} (ID: {contest_id})...")
            fetch_ranking(contest_id, output_dir, contest_name, year)
