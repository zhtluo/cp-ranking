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
def generate_urls(contests_yaml, key_map):
    # keys = contests_yaml["contests"]["keys"]
    years = contests_yaml["contests"]["years"]
    base_url = "https://icpc.global/api/contest/public"

    # iterate over *API spellings* (i.e. the keys in key_map)
    urls = {}
    for api_key, _canonical in key_map.items():
        for year in years:
            contest_name        = f"{api_key}-{year}"
            urls[contest_name]  = f"{base_url}/{contest_name}"
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

############# mapping split keys and such to the same format:
def build_key_map(contests_yaml):
    """
    Return a dict mapping *every* spelling that appears on ICPC’s web API
    to its canonical (human-friendly) region name.

    ─ keys (original behaviour) → themselves
    ─ split-keys["South-Central"] -> {"SCUSA": "South-Central",
                                      "South-Central-USA": "South-Central"}
    """
    mapping = {}

    # ordinary keys
    for k in contests_yaml["contests"]["keys"]:
        mapping[k] = k

    # split-keys
    for canonical, alts in contests_yaml["contests"]["split-keys"].items():
        for alt in alts:
            mapping[alt] = canonical

    return mapping

############# Main
if __name__ == "__main__":
    # Load contests.yaml
    contests_yaml = load_yaml("contests.yaml")
    key_map = build_key_map(contests_yaml)

    # Generate URLs
    urls = generate_urls(contests_yaml, key_map)

    # Fetch and organize data, grouping by CANONICAL region name
    contest_data = {}
    for contest_name, url in urls.items():
        print(f"Fetching data from {url}...")
        contest_id = fetch_contest_id(url)
        if contest_id:
            api_key, year = contest_name.rsplit("-", 1)
            canonical     = key_map.get(api_key, api_key)
            contest_data.setdefault(canonical, {})[year] = contest_id

    # Save to output YAML file
    output_dir = "./outputs"
    output_path = output_dir + "/contest_ids.yaml"
    APPEND_MODE = True

    if APPEND_MODE:
        print("Append mode ON — existing data will be preserved.")
        existing = load_yaml(output_path)

        # Merge without clobbering existing years
        merged = deepcopy(existing)
        changed_smth = False
        for key, year_map in contest_data.items():
            merged.setdefault(key, {})
            for year, cid in year_map.items():
                if year not in merged[key]:
                    print(f"--Adding {year} to {key}")
                    changed_smth = True
                elif merged[key][year] != cid:
                    print(f"[WARN] Updated Contest ID: {key} for {year} is set"\
                          f" to {merged[key][year]} but is found to be {cid}")
                merged[key].setdefault(year, cid)
        if not changed_smth:
            print("No data updated")
        final_data = merged
    else:
        print("Append mode OFF — file will be overwritten.")
        final_data = contest_data

    save_to_yaml(contest_data, output_path)
