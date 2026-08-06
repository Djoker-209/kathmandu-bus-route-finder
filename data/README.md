# Data

**Owner:** Dipesh S Saud — Scrum tasks 1–8
(schema, ingestion, cleaning, spatial queries, data access layer)

```
data/
├── raw/          Original exports
│                   - 2013 Yatayat OSM export
│                   - Overpass Turbo pulls
│                   - DOTM records
│
├── processed/    Cleaned, deduplicated, validated CSVs ready for DB import
│                   (see processed/README.md)
│
└── scripts/      ETL scripts
                    - dedup (~30m threshold)
                    - coordinate validation
                    - name normalization
```

`schema.sql` and `import.sql` at the top of `data/` build the full schema
(including `fare_rules`, added this round) and load everything in
`processed/`.

> **This is the confirmed single source of truth.**
> The earlier duplicate at `backend/app/db/schema.sql` was a stale,
> unmaintained mirror of an older/unrelated Alembic scaffold
> (`0001_initial_schema` — integer PKs, no `operators` / `fare_rules` /
> `route_operators` tables) and has been deleted. The live app database is
> migrated via Alembic revision `0002_replace_with_full_schema`, which
> replicates `data/schema.sql` table-for-table and has been applied and
> verified against a live instance.

---

## Pipeline order

1. **`raw/` → `processed/`**
   Original exports (2013 Yatayat OSM export, Overpass Turbo pulls, DOTM
   records) cleaned, deduplicated (~30m stop-merge threshold),
   coordinate-validated, and name-normalized into `processed/*_clean.csv`.
   See `processed/README.md` for the full cleaning methodology and
   `report_v4.md` for the audit trail.

2. **`schema.sql`**
   Builds the full schema — 7 tables:
     - `operators`
     - `stops`
     - `routes`
     - `route_stops`
     - `route_operators`
     - `route_return_leg_priority`
     - `fare_rules`

   Target: PostgreSQL 16.14 + PostGIS 3.4.2.
   Applied via Alembic migration `0002_replace_with_full_schema` in the
   backend's migration chain, so the live app DB and this file stay in
   sync going forward.

3. **`import.sql`**
   Loads all `processed/*_clean.csv` files directly via `\copy` into the
   schema from step 2, in dependency order:

   ```
   operators
     └─ stops
          └─ routes
               ├─ route_stops
               ├─ route_operators
               └─ route_return_leg_priority
   fare_rules   (independent — no FK dependencies)
   ```

   Followed by a built-in referential-integrity sanity check (orphan FKs,
   `total_stops` consistency, missing `geom`) — all currently passing
   clean.

   > **Before running:** paths inside `import.sql` are placeholders
   > (`/path/to/csv/`). Replace with your local absolute path to
   > `processed/` first.

---

## Current dataset status

| Table              | Row count |
|--------------------|-----------|
| `routes`           | 87        |
| `stops`             | 300       |
| `operators`         | 28        |
| `route_stops`       | 1,589     |
| `route_operators`   | 85        |
| `fare_rules`        | 5         |

All of the above are confirmed loaded successfully into a live
PostgreSQL 16.14 + PostGIS 3.4.2 instance via `import.sql`.

**Referential-integrity audit** — passed clean end-to-end:
  - `route_stops → stops` orphan check: **0**
  - `route_stops → routes` orphan check: **0**
  - `route_operators → operators` orphan check: **0**
  - `routes.total_stops` vs. actual `route_stops` count: **0 mismatches**
  - `stops` rows missing `geom`: **0**

  See `processed/README.md` and `report_v4.md` for the full audit trail.

**Fare rules** — 5 distance bands, confirmed non-overlapping (enforced by
the `EXCLUDE USING gist` constraint) and correctly computed as
`[min_distance_km, max_distance_km)`.
  > Note: all 5 rows are currently `desk_estimate_2026-08` — scaled from a
  > prior Bagmati Province rate, pending confirmation against the official
  > gazette notice. **Not yet field-verified.**

**Field verification status** — not re-assessed this round.
  <!-- TODO: replace with current Tier 1/2/3 breakdown -->
  Note: `return_leg_verification_priority_clean.csv` still flags **86 of
  87 routes** as pending return-leg verification, so most of the dataset
  likely isn't field-verified yet even though it's now referentially clean.

**Unresolved operator matches** — 3 routes have no confirmed operator
(`operator_id = NULL`):
  - `R2295986`
  - `R2295974`
  - `R2301161`

  Source listed `operator = "Local Microbus"` — an informal placeholder
  with no registered match.
