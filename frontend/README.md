# Frontend (Next.js + TypeScript + Leaflet)

Search for a stop-to-stop bus route across the Kathmandu Valley and see it
drawn on an interactive map, with live data from the FastAPI backend.

## Running locally

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000. By default the app talks to the backend at
`http://localhost:8000` — override this with an env var if your backend runs
elsewhere:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## What's here

- `app/page.tsx` — top-level layout, stop-list loading, and the
  `/route-finder` search flow.
- `components/SearchForm.tsx` — origin/destination inputs with autocomplete,
  a swap button, and a "Use my location" button backed by `/stops/nearby`.
- `components/BusMap.tsx` — imperative Leaflet map: draws each route leg as a
  colored polyline (dashed for walking transfers), with distinct markers for
  the trip's origin, destination, and any transfer points, road-following
  geometry from OSRM when available, and a legend.
- `types/route.ts` — mirrors `backend/app/schemas.py`. Keep in sync if the
  backend's response shapes change.

## Notes

- The map only renders client-side (`next/dynamic` with `ssr: false`), since
  Leaflet touches `window`.
- `SearchForm` resolves typed stop names to `stop_id`s via the loaded stop
  list — the `<datalist>` autocomplete is a soft suggestion, so submitting a
  name that doesn't match one of the suggestions surfaces an inline error
  rather than hitting the API with garbage.
- Backend "no route found" is a 404, so the frontend adds a client-side
  `found: boolean` to distinguish "no route" from a real error.
