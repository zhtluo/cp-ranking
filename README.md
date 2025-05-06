Our paper detailing this analysis is available at [insert arxiv link here]

# Overview
CP-Ranking has three primary processes:
1. ```fetch-contest-id.py```
  1. Reads ```contests.yaml``` for tags retrieved manually from (icpc.global/regionals/results)[https://icpc.global/regionals/results/2024].  Caution is necessary to verify that a tag is available for every year requested in ```contests.yaml:contests"years```.  Some contests changed names during a certain year.  Use ```contests:split-keys:``` for these cases, with the desired primary identifier as the key for each cluster of tags.
  2. Retrieves all contest results from ```icpc.global```'s publicly accessible records and stores them in ```outputs/rankings/*``` per year.
# Modifying CP-Ranking
## 
