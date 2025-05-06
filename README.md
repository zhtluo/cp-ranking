Our paper detailing this analysis is available at (insert arxiv link here)[].

# Overview
CP-Ranking has three primary processes:
1. ```fetch-contest-id.py```
  1. Reads ```contests.yaml``` for tags retrieved manually from [icpc.global/regionals/results](https://icpc.global/regionals/results/2024).  Caution is necessary to verify that a tag is available for every year requested in ```contests.yaml:contests"years```.  Some contests changed names after a certain year.  Use ```contests:split-keys:``` for these cases, with the desired primary identifier as the key for each cluster of tags.
  2. Retrieves all internal IDs for every dataset (every region, every year required in ```contests.yaml```) and stores them in ```outputs/contest_ids.yaml```.  This is necessary to retrieve the contest results from the ```icpc.global``` API with all required metadata properly.  Different options are available, including an ```append_mode``` to prevent overwriting previous downloads.  These results should not change as long as ```icpc.global```'s API remains the same, and a warning will appear if a different ID is ever detected.  If less data processing is desired, ```append_mode``` can be turned off to remove previous entries and limit analysis.

2. ```fetch-contest-ranking.py```: Fairly straightforward, this takes the IDs retrieved previously from ```outputs/contest_ids.yaml``` and downloads that dataset with all required metadata to ```rankings/*``` (per primary key -- for split keys -- per year); data is converted to ```yaml``` format.  By default will not download already downloaded data, but this setting can be turned off (```SKIP_PREV_GENERATED```).

3. ```compute_tau.py```: Arguably the most important step, this loads ```contests.yaml``` for reference and computes the Kendall Tau value between all ```contests:pairs:*``` and between codeforces (data manually retrieved and stored in ```cf-rating/*```, see paper for details) and every contest ID under ```contests:cf:*```.  By default, it prints to terminal, since we hackily used `\b` in ```:process_pairs_with_cf(...)``` to backspace in the output, and those weren't rendering properly when written directly to a file.
  * Importantly, a summary of all years that were processed prints at the beginning of the output.  We attempt to explain years that were skipped with four indicators:
```
* indicates skipped due to only 1 team to compare to
! indicates skipped due to 0 teams advancing to finals
# indicates this region is now a subregional (comparing to worlds)
otherwise skipped due to lack of data file
```
  So, for example: ```Processing comparison: World-Finals vs SEERC (for years = 2023, 2022, 2020, 2019, 2018, 2017)  -------- Skipped: 2024#, 2021!, 2016, 2015``` means 2024 was skipped because it's now a subregional, 2021 because no teams advanced to finals (usually indicating some sort of misunderstanding of what happened this year, or COVID), and 2015 and 16 simply don't have data available.  In this case, SEERC likely wasn't a contest in 2015 and 16.

# Modifying CP-Ranking
This is pretty easy.
1. Retrieve a tag for a region you want to add to the analysis from [icpc.global/regionals/results](https://icpc.global/regionals/results/2024).
2. Add it to ```contests.yaml:contests:keys``` or ```contests.yaml:contests:split-keys``` if the tag changes over the years you want to analyze.
  * Verify it is available under this tag for all the years under ```contests.yaml:contests:years:```, or be prepared for reports of missing data in the final ```compute_tau.py```.

    This shows available data: https://icpc.global/regionals/finder/Mid-Central-USA-2024/standings, this is an example of unavailable data: https://icpc.global/regionals/finder/Mid-Atlantic-USA-2024/standings.
  * Add it to be analyzed under ```contests.yaml:contests:pairs:``` (recommended) or ```:contests:cf:```, depending on what you want to compare.  Codeforces data is only available for 2020-2024, and has already been compared with all superregionals for the last 10 years.  Other comparisons with CF are unlikely to produce meaningful results as concentration of available tags associated with teams decreases quickly the further away from World Finals one gets.
3. All done!  Run ```fetch-contest-id.py```, ```fetch-contest-ranking.py```, and ```compute_tau.py```.

# Debugging
The lists on codeforces frequently do not match exactly with the data retrieved from ```icpc.global```.  Within datasets from ```icpc.global```, one university has the same name across all contests (even back-propagating through the years).  Name changes also happen for universities, which gets updated when running ```fetch-contest-ranking.py```, but the codeforces files were updated with a script not available here.  Furthermore, ```icpc.global``` encodes unicode with escaped strings and the codeforces data just has unicode.

Due to this, we present ```spotthediff_cf_vs_worlds.py``` to list out universities that do not appear in either worlds data or codeforces data.  The ones that only appear in codeforces should be the primary focus, since some world's teams don't have codeforces rankings. This was highly annoying to get right, but we ended up using a unicode normalizer (implemented in ```compute_tau.py```).  
  * *Many* methods did not work, so be exceedingly careful if you edit that function.

From there, we manually modified the codeforces data to match (e.g. changing ```technical university of munich``` to ```technische universitat munchen``` or ```universidad de guadalajara - cucei``` to ```universidad de guadalajara cucei```).

# Credits
Created by Zhongtang Luo and Ethan Dickey in F24-S25.  Please credit the original repository and paper referenced at the top of this readme when sharing.
