# Dropping this into `kathmandu-bus-route-finder/frontend/`

This scaffold was hand-written (no `npx create-next-app` was run) because it
was generated somewhere without npm registry access. Steps to get it running:

1. Copy every file in this folder into your repo's `frontend/` directory,
   replacing the placeholder `README.md` if needed (keep it, just add these
   alongside).

2. Install dependencies:
   ```
   cd frontend
   npm install
   ```

3. Run the dev server:
   ```
   npm run dev
   ```
   Visit http://localhost:3000 — you should see the search form on the left
   and a Kathmandu-centered Leaflet map on the right.

4. Try a search. Typing any two different stop names (autocomplete suggests
   the 5 mock stops: Ratna Park, Koteshwor, Kalanki, Lagankhel, Balaju) and
   hitting "Find route" returns a fake single-transfer route with two colored
   polylines and markers. Typing the same stop for both fields exercises the
   "no route found" state.

## What's mocked vs. real

- `lib/mockRoute.ts` — fake stops and fake `/route/search` responses. This is
  the file you'll delete once the backend is live.
- `types/route.ts` — the proposed JSON contract (`stops`, `routes`,
  `route_stops` per the proposal). **Confirm the exact field names with
  Janak/Dipesh before they lock their Pydantic schemas**, then update this
  file to match exactly — it's the single source of truth the rest of the
  frontend is typed against.
- `app/page.tsx` — has a clearly marked `MOCK BLOCK` in `handleSearch`. When
  the real API exists, delete that block and uncomment the `fetch(...)` call
  above it.

## Next steps in order

1. Get this running locally and confirm the map renders.
2. Sync with Janak/Dipesh on the `/route/search` request/response schema —
   update `types/route.ts` and `lib/mockRoute.ts` to match exactly.
3. Once mock rendering looks right, integrate OSRM: convert each leg's
   straight `path` into a real road-following polyline by calling OSRM's
   `/route/v1/driving/{lng},{lat};{lng},{lat}` endpoint (or `/foot/` if
   walking legs matter) and use the returned geometry instead of the two-point
   line.
4. When the FastAPI endpoint is live, swap the mock block in `page.tsx` for
   the real fetch call, and handle non-200 responses.
