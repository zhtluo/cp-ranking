#!/usr/bin/env python3
import yaml
from compute_tau import normalize

def load_institutions(path, key):
    with open(path) as f:
        data = yaml.safe_load(f)
    # key = 'institution' or 'university'
    entries = {entry[key] for entry in data if entry.get(key)}
    # return both the raw names and their normalized forms
    return {normalize(n) for n in entries}

if __name__ == '__main__':
    year = "2024"
    insts = load_institutions(f'outputs/rankings/World-Finals_{year}_ranking.yaml', 'institution')
    unis  = load_institutions(f'cf-rating/{year}.yaml',        'university')

    common        = insts & unis
    only_rankings = insts - unis
    only_ratings  = unis - insts

    print(f"Common institutions ({len(common)}):")
    if common:
        for name in sorted(common):
            print(f"  • {name}")
    else:
        print("  (none)")

    print(f"\nOnly in World Finals ranking ({len(only_rankings)}):")
    if only_rankings:
        for name in sorted(only_rankings):
            print(f"  • {name}")
    else:
        print("  (none)")

    print(f"\nOnly in CF‑rating list ({len(only_ratings)}):")
    if only_ratings:
        for name in sorted(only_ratings):
            print(f"  • {name}")
    else:
        print("  (none)")
