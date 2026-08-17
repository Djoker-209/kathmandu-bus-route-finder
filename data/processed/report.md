# Orphan-pair audit & cleanup report — Kathmandu Bus Route Finder

_Generated 2026-08-17T03:46:04Z by scripts/clean_data.py_

| Table | Rows before | Rows after |
|---|---|---|
| operators.csv | 29 | 29 |
| stops.csv | 317 | 317 |
| routes.csv | 94 | 94 |
| route_stops.csv | 1818 | 1818 |
| route_operators.csv | 92 | 92 |

## 1. route_stops orphan pairs
- Removed rows: 0

## 2. route_stops re-sequencing
- Routes re-sequenced (1..N, order preserved): 94

## 2b. Stop deduplication (~250m radius candidates)
- Stops actually merged (human-confirmed via stop_dedup_overrides.yaml): 0
- Candidate clusters PENDING human review (not merged): 55
  Distance alone can't tell 'same stop, different name' from 'different nearby stops' —
  add confirmed pairs to data/scripts/stop_dedup_overrides.yaml to merge them:
    - ['S0005', 'S0206']
    - ['S0011', 'S0182']
    - ['S0012', 'S0045']
    - ['S0013', 'S0171', 'S0236']
    - ['S0015', 'S0033']
    - ['S0020', 'S0366']
    - ['S0021', 'S0110']
    - ['S0028', 'S0099']
    - ['S0030', 'S0044', 'S0336']
    - ['S0031', 'S0137']
    - ['S0034', 'S0062']
    - ['S0035', 'S0348']
    - ['S0037', 'S0269']
    - ['S0046', 'S0222']
    - ['S0050', 'S0165']
    - ['S0051', 'S0197']
    - ['S0055', 'S0340']
    - ['S0056', 'S0277']
    - ['S0058', 'S0116']
    - ['S0059', 'S0205']
    - ['S0063', 'S0235']
    - ['S0064', 'S0345']
    - ['S0067', 'S0076', 'S0278']
    - ['S0068', 'S0351']
    - ['S0069', 'S0074', 'S0114']
    - ['S0075', 'S0091', 'S0167']
    - ['S0080', 'S0202']
    - ['S0086', 'S0198']
    - ['S0094', 'S0339']
    - ['S0096', 'S0176']
    - ['S0097', 'S0132']
    - ['S0103', 'S0175']
    - ['S0108', 'S0304']
    - ['S0112', 'S0155', 'S0223', 'S0368']
    - ['S0113', 'S0349']
    - ['S0115', 'S0180']
    - ['S0122', 'S0229']
    - ['S0124', 'S0337']
    - ['S0133', 'S0367']
    - ['S0142', 'S0234']
    - ['S0152', 'S0166']
    - ['S0154', 'S0227']
    - ['S0158', 'S0238']
    - ['S0159', 'S0215']
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
- Routes actually merged (human-confirmed via route_dedup_overrides.yaml): 0
- Marked is_bidirectional as a result of merge: []
- Candidate pairs PENDING human review (not merged): 17
    - R2909799 ("Kamalbinayak-Ratnapark") <-> R2988890 ("Bagbazaar-Kamalbinayak") — stop-set similarity 0.8
    - R2909799 ("Kamalbinayak-Ratnapark") <-> R2988893 ("Ratnapark-Changu") — stop-set similarity 0.73
    - R2909799 ("Kamalbinayak-Ratnapark") <-> R2989027 ("Changu-Ratnapark") — stop-set similarity 0.92
    - R2988890 ("Bagbazaar-Kamalbinayak") <-> R2988893 ("Ratnapark-Changu") — stop-set similarity 0.92
    - R2988890 ("Bagbazaar-Kamalbinayak") <-> R2989027 ("Changu-Ratnapark") — stop-set similarity 0.73
    - R2988893 ("Ratnapark-Changu") <-> R2989027 ("Changu-Ratnapark") — stop-set similarity 0.79
    - R2988983 ("Chyamasingh to Ratnapark") <-> R2989052 ("Ratna Park - Chyamasingh") — stop-set similarity 0.76
    - R2295734 ("Ratna Park-Budhanilkantha School") <-> R2323381 ("Budhanilkantha School- Ratna Park") — stop-set similarity 0.94
    - R2301205 ("Purano Bus Park-Shivapuri") <-> R2301206 ("Shivapuri-Purano Bus Park") — stop-set similarity 0.73
    - R3068536 ("Kalanki- Lagankhel") <-> R3068548 ("Lagankhel - Kalanki") — stop-set similarity 1.0 [EXACT REVERSE — likely a clean bidirectional pair]
    - R2301263 ("Chakrapath Parikrama") <-> R3102605 ("Swyambhu-Chakrapath parikrama") — stop-set similarity 0.97
    - R2282031 ("Ratna Park - Kirtipur") <-> R3020213 ("Ratna Park - Panga Dobato- Dhokashi") — stop-set similarity 0.82
    - R2282031 ("Ratna Park - Kirtipur") <-> R3020231 ("Ratna Park - Panga Dobato- Nagaun- Bhatkepati") — stop-set similarity 0.88
    - R3020212 ("Dhokashi- Chobar gate- Ratnapark") <-> R3020213 ("Ratna Park - Panga Dobato- Dhokashi") — stop-set similarity 0.75
    - R3020213 ("Ratna Park - Panga Dobato- Dhokashi") <-> R3020231 ("Ratna Park - Panga Dobato- Nagaun- Bhatkepati") — stop-set similarity 0.82
    - R2295902 ("KattyaniChowk-Sundhara") <-> R2295903 ("Sundhara-Milanchowk-KattyaniChowk") — stop-set similarity 0.75
    - R2295902 ("KattyaniChowk-Sundhara") <-> R2295941 ("Old Baneshwar-Sundhara") — stop-set similarity 0.72

## 3a. routes.start_stop_id / end_stop_id / total_stops recomputation
- start_stop_id corrected: 0 -> []
- end_stop_id corrected:   0 -> []
- total_stops corrected:   0 -> []

## 3b. Default bidirectional/status override
- All non-loop routes forced to is_bidirectional=True; all routes forced to status='active'. See apply_default_bidirectional_and_status() docstring for why.

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
- 31 route_stops rows revisit a stop_id already used earlier in the same route, across 21 routes — consistent with loop/return-leg routes. Left untouched.