# Orphan-pair audit & cleanup report — Kathmandu Bus Route Finder

_Generated 2026-08-08T06:00:05Z by scripts/clean_data.py_

| Table | Rows before | Rows after |
|---|---|---|
| operators.csv | 29 | 29 |
| stops.csv | 317 | 302 |
| routes.csv | 94 | 88 |
| route_stops.csv | 1818 | 1662 |
| route_operators.csv | 92 | 86 |

## 1. route_stops orphan pairs
- Removed rows: 0

## 2. route_stops re-sequencing
- Routes re-sequenced (1..N, order preserved): 94

## 2b. Stop deduplication (~250m radius candidates)
- Stops actually merged (human-confirmed via stop_dedup_overrides.yaml): 15
    - kept S0069, dropped ['S0074']
    - kept S0069, dropped ['S0091']
    - kept S0055, dropped ['S0340']
    - kept S0005, dropped ['S0206']
    - kept S0045, dropped ['S0012']
    - kept S0110, dropped ['S0021']
    - kept S0269, dropped ['S0037']
    - kept S0044, dropped ['S0336']
    - kept S0056, dropped ['S0277']
    - kept S0063, dropped ['S0235']
    - kept S0345, dropped ['S0064']
    - kept S0202, dropped ['S0080']
    - kept S0103, dropped ['S0175']
    - kept S0229, dropped ['S0122']
    - kept S0159, dropped ['S0215']
- Candidate clusters PENDING human review (not merged): 40
  Distance alone can't tell 'same stop, different name' from 'different nearby stops' —
  add confirmed pairs to data/scripts/stop_dedup_overrides.yaml to merge them:
    - ['S0011', 'S0182']
    - ['S0013', 'S0171', 'S0236']
    - ['S0015', 'S0033']
    - ['S0020', 'S0366']
    - ['S0028', 'S0099']
    - ['S0031', 'S0137']
    - ['S0034', 'S0062']
    - ['S0035', 'S0348']
    - ['S0046', 'S0222']
    - ['S0050', 'S0165']
    - ['S0051', 'S0197']
    - ['S0058', 'S0116']
    - ['S0059', 'S0205']
    - ['S0067', 'S0076', 'S0278']
    - ['S0068', 'S0351']
    - ['S0086', 'S0198']
    - ['S0094', 'S0339']
    - ['S0096', 'S0176']
    - ['S0097', 'S0132']
    - ['S0108', 'S0304']
    - ['S0112', 'S0155', 'S0223', 'S0368']
    - ['S0113', 'S0349']
    - ['S0115', 'S0180']
    - ['S0124', 'S0337']
    - ['S0133', 'S0367']
    - ['S0142', 'S0234']
    - ['S0152', 'S0166']
    - ['S0154', 'S0227']
    - ['S0158', 'S0238']
    - ['S0172', 'S0355']
    - ['S0194', 'S0219']
    - ['S0207', 'S0241', 'S0193']
    - ['S0210', 'S0338']
    - ['S0221', 'S0047']
    - ['S0225', 'S0230']
    - ['S0244', 'S0250']
    - ['S0256', 'S0262']
    - ['S0081', 'S0161']
    - ['S0283', 'S0284']
    - ['S0356', 'S0357']

## 2c. Route deduplication (same operator + similar stop set)
- Routes actually merged (human-confirmed via route_dedup_overrides.yaml): 6
    - kept R3068536, dropped R3068548
    - kept R2295734, dropped R2323381
    - kept R2988893, dropped R2989027
    - kept R2988983, dropped R2989052
    - kept R2301205, dropped R2301206
    - kept R3102605, dropped R2301263
- Marked is_bidirectional as a result of merge: ['R3068536', 'R2295734', 'R2988893', 'R2988983', 'R2301205']
- Candidate pairs PENDING human review (not merged): 9
    - R2909799 ("Kamalbinayak-Ratnapark") <-> R2988890 ("Bagbazaar-Kamalbinayak") — stop-set similarity 0.86
    - R2909799 ("Kamalbinayak-Ratnapark") <-> R2988893 ("Ratnapark-Changu") — stop-set similarity 0.78
    - R2988890 ("Bagbazaar-Kamalbinayak") <-> R2988893 ("Ratnapark-Changu") — stop-set similarity 0.91
    - R2282031 ("Ratna Park - Kirtipur") <-> R3020213 ("Ratna Park - Panga Dobato- Dhokashi") — stop-set similarity 0.82
    - R2282031 ("Ratna Park - Kirtipur") <-> R3020231 ("Ratna Park - Panga Dobato- Nagaun- Bhatkepati") — stop-set similarity 0.88
    - R3020212 ("Dhokashi- Chobar gate- Ratnapark") <-> R3020213 ("Ratna Park - Panga Dobato- Dhokashi") — stop-set similarity 0.75
    - R3020213 ("Ratna Park - Panga Dobato- Dhokashi") <-> R3020231 ("Ratna Park - Panga Dobato- Nagaun- Bhatkepati") — stop-set similarity 0.82
    - R2295902 ("KattyaniChowk-Sundhara") <-> R2295903 ("Sundhara-Milanchowk-KattyaniChowk") — stop-set similarity 0.75
    - R2295902 ("KattyaniChowk-Sundhara") <-> R2295941 ("Old Baneshwar-Sundhara") — stop-set similarity 0.72

## 3. routes.start_stop_id / end_stop_id / total_stops recomputation
- start_stop_id corrected: 2 -> ['R3232098', 'R3204165']
- end_stop_id corrected:   4 -> ['R2276770', 'R3102319', 'R2295974', 'R2988806']
- total_stops corrected:   0 -> []

## 4. routes.operator_id orphan references
- Invalid operator_id value(s): []
- Routes nulled (unrecoverable): 0 -> []

## 5. Distance outlier flags
- Routes flagged distance_flagged_for_recompute: 0 -> []

## 6. Post-cleanup verification (must all read 0)
- route_stops.stop_id not in stops: 0
- route_stops.route_id not in routes: 0
- route_operators.route_id not in routes: 0
- route_operators.operator_id not in operators: 0
- routes.operator_id not in operators (excl. NULL): 0
- routes.start_stop_id not in stops: 0
- routes.end_stop_id not in stops: 0
- routes.total_stops mismatched vs actual route_stops count: 0

## 7. Note — revisited stops (informational only, not modified)
- 97 route_stops rows revisit a stop_id already used earlier in the same route, across 35 routes — consistent with loop/return-leg routes. Left untouched.