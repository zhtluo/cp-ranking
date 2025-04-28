import yaml
import requests
import os
from copy import deepcopy

############# YAML
# Load the YAML file
def load_yaml(file_path):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)

# Save data to a YAML file
def save_to_yaml(data, file_path):
    # Create directories if needed
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as file:
        yaml.dump(data, file, default_flow_style=False)
        print(f"Data saved to {file_path}")


############# html stuff
# Generate URLs from contest keys and years
def generate_urls(contests_yaml):
    keys = contests_yaml["contests"]["keys"]
    years = contests_yaml["contests"]["years"]
    base_url = "https://icpc.global/api/contest/public"

    urls = {}
    for key in keys:
        for year in years:
            contest_name = f"{key}-{year}"
            urls[contest_name] = f"{base_url}/{contest_name}"
    return urls


# Fetch contest ID from a URL
def fetch_contest_id(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for HTTP errors
        data = response.json()
        return data.get("id")  # Return the 'id' field from the JSON data
    except requests.RequestException as e:
        print(f"Failed to fetch data from {url}: {e}")
        return None



# Main script
if __name__ == "__main__":
    # Load contests.yaml
    contests = load_yaml("contests.yaml")

    # Generate URLs
    urls = generate_urls(contests)

    # Fetch and organize data
    contest_data = {}
    for contest_name, url in urls.items():
        print(f"Fetching data from {url}...")
        contest_id = fetch_contest_id(url)
        if contest_id:
            key, year = contest_name.rsplit("-", 1)
            if key not in contest_data:
                contest_data[key] = {}
            contest_data[key][year] = contest_id

    # Save to output YAML file
    output_dir = "./outputs"
    output_path = output_dir + "/contest_ids.yaml"
    APPEND_MODE = True

    if APPEND_MODE:
        print("Append mode ON — existing data will be preserved.")
        existing = load_yaml(output_path)

        # Merge without clobbering existing years
        merged = deepcopy(existing)
        for key, year_map in contest_data.items():
            merged.setdefault(key, {})
            for year, cid in year_map.items():
                merged[key].setdefault(year, cid)
        final_data = merged
    else:
        print("Append mode OFF — file will be overwritten.")
        final_data = contest_data

    save_to_yaml(contest_data, output_path)
