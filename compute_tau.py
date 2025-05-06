import yaml
from scipy.stats import kendalltau
import os
import math
from collections import defaultdict
from unidecode import unidecode
import unicodedata
# import re
# import codecs
from ftfy import fix_text

def normalize(name: str, lowerit=True) -> str:
    # # 1) turn ANY accent/mojibake into plain ASCII
    # name = unidecode(name)
    # 1) Decompose into base characters + combining marks (NFD or NFKD)
    name = fix_text(name)
    decomposed = unicodedata.normalize('NFKD', name)
    # 2) Filter out all combining characters (category 'Mn')
    finished = (''.join(ch for ch in decomposed if unicodedata.category(ch) != 'Mn'))
    if lowerit:
        finished = finished.lower().strip()
    return finished
    # name = unicodedata.normalize('NFKD', name) \
    #      .encode('ascii', 'ignore') \
    #      .decode('ascii')
    # return name

    # # 1) repair common UTF-8 mojibake: bytes that were read as Latin‑1
    # # 1) repair only real mojibake (Ã + something)
    # if 'Ã' in name:
    #     try:
    #         name = name.encode('latin1').decode('utf8')
    #     except (UnicodeEncodeError, UnicodeDecodeError) as e:
    #         # if it wasn't mojibake, just leave it
    #         print("WARN WARN WARN ERROR in decoding/normalizing university names: ", e)
    #         pass
    #
    # # 2) decode any Python-style \xNN escapes (if your YAML ever has them)
    # # decode any Python-style \xNN escapes in the string, e.g. "\xFC" → ü
    # # 2) decode Python-style escapes if present
    # if '\\x' in name or '\\u' in name:
    #     try:
    #         name = codecs.decode(name, 'unicode_escape')
    #     except Exception as e:
    #         # if it wasn’t encoded with \x escapes, just leave it
    #         print("WARN WARN WARN ERROR in decoding/normalizing university names: ", e)
    #         pass
    #
    # # decompose accents (ü → u + ¨), then drop non‑ASCII
    # name = unicodedata.normalize('NFKD', name)
    # name = name.encode('ascii', 'ignore').decode('ascii')
    # # strip common prefixes
    # name = re.sub(r'^(eth|univ|university)\s+', '', name, flags=re.I)
    # return name.lower().strip()

# Load the YAML configuration file.
def load_yaml(file_path):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


# Load the ranking file in YAML format and assign index as rank if rank is null.
def load_ranking(file_path):
    with open(file_path, "r") as file:
        rankings = yaml.safe_load(file)

    # Filter out entries with invalid data
    valid_rankings = [
        entry
        for entry in rankings
        if entry.get("institution")
        and isinstance(entry.get("problemsSolved"), int)
        and entry["problemsSolved"] > 0
    ]

    # Sort by problems solved (descending) and then by total time (ascending)
    sorted_rankings = sorted(
        valid_rankings,
        key=lambda x: (-x["problemsSolved"], x.get("totalTime", float("inf"))),
    )

    # Create a dictionary to store the best-ranked team for each institution
    institution_rankings = {}
    for index, entry in enumerate(sorted_rankings, start=1):  # Assign ranks based on sorted order
        raw = entry["institution"]
        institution = normalize(raw)#get rid of stupid unicode stuff

        if (
            institution not in institution_rankings
            or index < institution_rankings[institution]["rank"]
        ):
            institution_rankings[institution] = {
                **entry,
                "rank": index,
                "_raw_name": raw,
            }  # Store with updated rank

    return institution_rankings


# Load CF rating file in YAML format and assign rank based on average CF rating.
def load_cf_ratings(file_path):
    with open(file_path, "r") as file:
        cf_data = yaml.safe_load(file)

    # Rank universities by CF rating (higher rating gets better rank)
    cf_data.sort(key=lambda x: -x["average_cf_rating"])  # Descending order

    cf_rankings = {}
    for rank, entry in enumerate(cf_data, start=1):
        raw = entry.get("university")
        if raw is None:
            continue
        university = normalize(raw)#get rid of stupid unicode stuff
        cf_rankings[university] = {
            "rank": rank,
            "average_cf_rating": entry["average_cf_rating"],
            "_raw_name": raw,
        }

    return cf_rankings


# Compare the rankings of two contests in a specific year using Kendall's Tau.
def compare_contests(year, contest1, contest2, rankings_dir):
    file1 = os.path.join(rankings_dir, f"{contest1}_{year}_ranking.yaml")
    file2 = os.path.join(rankings_dir, f"{contest2}_{year}_ranking.yaml")
    if not os.path.exists(file1) or not os.path.exists(file2):
        return None, -1

    rankings1 = load_ranking(file1)
    rankings2 = load_ranking(file2)

    # Find common institutions
    common_institutions = set(rankings1.keys()) & set(rankings2.keys())
    num_schools = len(common_institutions)

    # Skip if there's only one shared school
    if num_schools <= 1:
        return None, num_schools

    # Create ranking lists for the common institutions
    ranks1 = []
    ranks2 = []

    for institution in common_institutions:
        ranks1.append(rankings1[institution]["rank"])
        ranks2.append(rankings2[institution]["rank"])

    # Calculate Kendall's Tau
    tau, _ = kendalltau(ranks1, ranks2) #Returns tau, pvalue
    return tau, num_schools


# Compare a specific contest against CF ratings.
def compare_contests_with_cf(contest, cf_ratings_dir, rankings_dir, years):
    total_tau = 0
    total_pairs = 0
    yearly_results = {}

    for year in years:
        contest_file = os.path.join(rankings_dir, f"{contest}_{year}_ranking.yaml")
        cf_file = os.path.join(cf_ratings_dir, f"{year}.yaml")

        if not os.path.exists(contest_file) or not os.path.exists(cf_file):
            continue

        contest_rankings = load_ranking(contest_file)
        cf_rankings = load_cf_ratings(cf_file)

        # Find common institutions
        common_universities = set(contest_rankings.keys()) & set(cf_rankings.keys())
        num_schools = len(common_universities)

        if num_schools <= 1:
            continue

        # Create ranking lists
        ranks1 = []
        ranks2 = []

        for university in common_universities:
            ranks1.append(contest_rankings[university]["rank"])
            ranks2.append(cf_rankings[university]["rank"])

        # Calculate Kendall's Tau
        tau, _ = kendalltau(ranks1, ranks2) #Returns tau, pvalue
        if tau is not None and not math.isnan(tau):
            yearly_results[year] = {"tau": tau, "num_schools": num_schools}
            pairs = num_schools * (num_schools - 1) // 2
            total_tau += tau * pairs
            total_pairs += pairs

    if total_pairs == 0:
        weighted_average_tau = None
    else:
        weighted_average_tau = total_tau / total_pairs

    return yearly_results, weighted_average_tau


def process_pairs_with_cf(yaml_config, rankings_dir, cf_ratings_dir):
    """
    Process all comparisons specified in the YAML configuration, including CF ratings.

    Args:
    - yaml_config: Parsed YAML configuration.
    - rankings_dir: Directory where contest ranking files are stored.
    - cf_ratings_dir: Directory where CF rating files are stored.

    Returns:
    - results: Dictionary with results for CF ratings and pairwise contest comparisons.
    """
    years = yaml_config["contests"]["years"]
    pairs = yaml_config["contests"]["pairs"]
    cf_contests = yaml_config["contests"]["cf"]

    results = {}

    # Process comparisons between contests and CF ratings
    for contest in cf_contests:
        print(f"Processing comparison: {contest} vs CF Ratings")
        yearly_results, weighted_average_tau = compare_contests_with_cf(
            contest, cf_ratings_dir, rankings_dir, years
        )
        results[f"{contest}_vs_CF-Ratings"] = {
            "yearly_results": yearly_results,
            "weighted_average_tau": weighted_average_tau,
        }

    # Process other contest pairs
    print("  * indicates skipped due to only 1 team to compare to")
    print("  ! indicates skipped due to 0 teams advancing to finals")
    print("  # indicates this region is now a subregional (comparing to worlds)")
    print("  otherwise skipped due to lack of data file")
    for contest1, contest2 in pairs:
        #TODO: make this the same as CF above (same function and everything)
        print(f"Processing comparison: {contest1} vs {contest2} (for years =", end='')
        total_tau = 0
        total_pairs = 0
        yearly_results = {}
        skipped = []

        for year in years:
            tau, num_schools = compare_contests(year, contest1, contest2, rankings_dir)
            #EU championships started in 2024, don't compare subregionals to them.
            is_now_regional = False
            if (year > 2023) and (contest1 == "World-Finals") and \
               (contest2 in ['SEERC', 'Central-Europe', 'SWERC', 'Northwestern-Europe']):
                tau = None
                is_now_regional = True
            if tau is not None and not math.isnan(tau):
                print(" " + str(year) + ",", end='')
                yearly_results[year] = {"tau": tau, "num_schools": num_schools}
                pairs = num_schools * (num_schools - 1) // 2
                total_tau += tau * pairs
                total_pairs += pairs
            else:
                reason = str(year)
                if is_now_regional:
                    reason += "#"
                elif num_schools == 1:
                    reason += "*"
                elif num_schools == 0:
                    reason += "!"
                skipped.append(reason)
        #clean up skipped newline
        print("\b) " + (" -------- Skipped: " + ", ".join(skipped) if skipped else ""))

        if total_pairs == 0:
            weighted_average_tau = None
        else:
            weighted_average_tau = total_tau / total_pairs

        results[(contest1, contest2)] = {
            "yearly_results": yearly_results,
            "weighted_average_tau": weighted_average_tau,
        }

    return results


# Main
if __name__ == "__main__":
    # diff -qsy outputs/rankings_old/ICPCKolkataKanpur_2024_ranking.yaml outputs/rankings_old/ICPCKolkataKanpur_2024_ranking.yaml
    # https://github.com/zhtluo/cp-ranking/compare/3e0d141..391ae0b
    # Load YAML configuration
    yaml_file = "contests.yaml"
    config = load_yaml(yaml_file)

    # Rankings directory
    rankings_dir = "./outputs/rankings"

    # CF Ratings directory
    cf_ratings_dir = "./cf-rating"

    # Process comparisons
    pairwise_results = process_pairs_with_cf(config, rankings_dir, cf_ratings_dir)

    # Print results
    tables = defaultdict(list)      # table_name -> [(row, denom, tau)]
    print("\nComparison Results:")
    for key, data in pairwise_results.items():
        print(f"\nComparison: {key}")
        if not data["yearly_results"]:
            print("  No valid data found.")
            continue

        denom_pairs = 0
        for year, result in data["yearly_results"].items():
            n = result["num_schools"]
            denom_pairs += n*(n-1)//2
            print(f"  Year {year}: Tau = {result['tau']:.3f}, "\
                  f"Shared Schools = {n}")

        avg_tau = data["weighted_average_tau"]
        if avg_tau is None:
            print("  Weighted Average Tau: None (no valid years)")
        else:
            print(f"  Weighted Average Tau: {avg_tau:.3f}")
            print(f"  Pairs (denominator): {denom_pairs}")

        # for creating latex-ready tables:
        # decide which table this row belongs to
        if isinstance(key, tuple):
            table_name, row_label = key          # (contest1, contest2)
        else:                                    # e.g. "World-Finals_vs_CF-Ratings"
            row_label, _ = key.split("_vs_")
            table_name   = "codeforces"

        tables[table_name].append((row_label, denom_pairs, avg_tau))

    # emit the LaTeX rows
    for table_name, rows in tables.items():
        print(f"\n% ---- {table_name} ----")
        weighted_sum = 0
        weighted_den = 0

        for label, pairs, tau in rows:
            tau_str = "-" if tau is None else f"{tau:.3f}"
            print(f"        {label} & {pairs if pairs else '-'} & {tau_str} \\\\")
            if tau is not None:
                weighted_sum += tau * pairs
                weighted_den += pairs

        if weighted_den:                          # weighted average for the table
            wt_avg = weighted_sum / weighted_den
            print(f"        \\textbf{{Weighted Average}} & - & "
                  f"\\textbf{{{wt_avg:.3f}}} \\\\")
# ChatGPT on p-value reporting:
# Whether you display the p-value alongside Kendall’s τ depends on what you want the number to do for you:
#
# Goal	Typical practice
# Hypothesis testing (“Are the two rankings significantly associated?”)	Report τ, n, p-value (or at least mark significance with * or †).
# Descriptive agreement (“How strongly do they align, ignoring sampling error?”)	Report τ and n (or pairs); omit p-value.
# So if your table is meant as a descriptive comparison—​common in
#  information-retrieval, ranking-aggregation, or contest-analysis papers—​leaving
#  out the p-value is perfectly normal. If you want to make inferential claims
#  (“the correlation is significant at α = 0.05”), then you should show it (or
#  note the α-level).
# https://www.statisticshowto.com/kendalls-tau/
#Recommendations:
# For a concise agreement table (like the example you showed), τ and the pair
#  count are enough—​especially if readers can see that n ≥ 30, making small
#  τ values already informative.
# If reviewers or co-authors insist on statistical significance, add a
#  superscript “*” when p < 0.05 and explain the threshold in a caption;
#  that keeps the table readable without another numeric column.
