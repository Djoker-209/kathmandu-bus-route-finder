# Data

Owner: Dipesh S Saud — Scrum tasks 1-8 (schema, ingestion, cleaning, spatial queries, data access layer).

```
data/
├── raw/          Original exports (2013 Yatayat OSM export, Overpass Turbo pulls, DOTM records)
├── processed/    Cleaned, deduplicated, validated CSVs ready for DB import (see processed/README.md)
└── scripts/      ETL scripts: dedup (~30m threshold), coordinate validation, name normalization
```

`schema.sql` and `import.sql` at the top of `data/` build the full schema
(including `fare_rules`, added this round) and load everything in
`processed/`. <!-- TODO confirm: load_to_db.py currently points at
backend/app/db/schema.sql — reconcile with data/schema.sql before relying
on either path. -->

## Pipeline order

1. `scripts/import_raw.py` — load raw OSM/DOTM exports
2. `scripts/dedupe_stops.py` — merge stops within ~30m (Scrum 3)
3. `scripts/validate_coords.py` — reject out-of-bounds coordinates (Scrum 3)
4. `scripts/normalize_names.py` — lowercase/trim stop & route names for matching
5. `scripts/load_to_db.py` — insert into `stops`, `routes`, `route_stops` (uses `backend/app/db/schema.sql`) <!-- TODO: confirm this now also covers operators/route_operators/fare_rules, or update this step -->

## Current dataset status

* **87 routes**, **300 stops**, **28 operators**, **1589** route↔stop links,
  **85** route↔operator links, **5** fare bands (`fare_rules`) — all in
  `processed/`
* Referential-integrity audit (orphan FKs, type/bounds validation, schema
  constraints) passed clean end-to-end against a live PostgreSQL 16.14 +
  PostGIS 3.4.2 instance — see `processed/README.md` and `report_v4.md` for
  the full audit trail
* **Field verification status**: not re-assessed this round — `<!-- TODO:
  replace with current Tier 1/2/3 breakdown -->`. Note
  `return_leg_verification_priority_clean.csv` still flags 86 of 87 routes
  as pending return-leg verification, so most of the dataset likely isn't
  field-verified yet even though it's now referentially clean
* 3 routes (`R2295986`, `R2295974`, `R2301161`) have no confirmed operator
  (`operator_id = NULL`) — source listed `operator = "Local Microbus"`, an
  informal placeholder with no registered match
