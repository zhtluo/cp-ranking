import re
import os

# Input file
input_file = "data/raw.txt"

# Create a directory to store output files (optional)
output_dir = "data/"
os.makedirs(output_dir, exist_ok=True)

# Define the patterns for NOIP and NOI
noip_pattern = re.compile(r"(NOIP\d{4})")
noi_pattern = re.compile(r"(NOI\d{4})")
ioi_pattern = re.compile(r"(IOI\d{4})")

# Open the input file and process it
with open(input_file, "r", encoding="utf-8") as infile:
    for line in infile:
        # Check for NOIP+year
        noip_match = noip_pattern.search(line)
        if noip_match:
            filename = os.path.join(output_dir, f"{noip_match.group(1)}.csv")
            with open(filename, "a", encoding="utf-8") as outfile:
                outfile.write(line)
            continue

        # Check for NOI+year
        noi_match = noi_pattern.search(line)
        if noi_match:
            filename = os.path.join(output_dir, f"{noi_match.group(1)}.csv")
            with open(filename, "a", encoding="utf-8") as outfile:
                outfile.write(line)
            continue

        # Check for IOI+year
        ioi_match = ioi_pattern.search(line)
        if ioi_match:
            filename = os.path.join(output_dir, f"{ioi_match.group(1)}.csv")
            with open(filename, "a", encoding="utf-8") as outfile:
                outfile.write(line)
            continue

print(f"Data has been split into individual files in the '{output_dir}' directory.")
