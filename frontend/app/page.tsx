"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import SearchForm from "@/components/SearchForm";
import { RouteSearchResult, Stop } from "@/types/route";

// Leaflet touches `window`, so the map must load client-side only.
const BusMap = dynamic(() => import("@/components/BusMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center text-sm text-neutral-500">
      Loading map…
    </div>
  ),
});

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function formatDuration(totalSeconds: number): string {
  const minutes = Math.round(totalSeconds / 60);
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  return remaining === 0 ? `${hours} hr` : `${hours} hr ${remaining} min`;
}

export default function Home() {
  const [stops, setStops] = useState<Stop[]>([]);
  const [stopsLoading, setStopsLoading] = useState(true);
  const [stopsError, setStopsError] = useState(false);
  const [result, setResult] = useState<RouteSearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load the full stop list for the autocomplete datalist, paging through
  // /stops since `limit` is capped server-side by settings.MAX_PAGE_SIZE.
  useEffect(() => {
    async function loadStops() {
      try {
        const all: Stop[] = [];
        let offset = 0;
        const pageSize = 100; // stays under MAX_PAGE_SIZE regardless of its exact value

        while (true) {
          const res = await fetch(`${API_BASE}/stops?limit=${pageSize}&offset=${offset}`);
          if (!res.ok) {
            setStopsError(true);
            break;
          }
          const data: { total: number; items: Stop[] } = await res.json();
          all.push(...data.items);
          offset += pageSize;
          if (offset >= data.total || data.items.length === 0) break;
        }

        setStops(all);
      } catch {
        // Search still works if the user knows a stop_id, but the
        // autocomplete/"use my location" affordances need this list.
        setStopsError(true);
      } finally {
        setStopsLoading(false);
      }
    }
    loadStops();
  }, []);

  async function handleSearch(originId: string, destinationId: string) {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const params = new URLSearchParams({
        origin: originId,
        destination: destinationId,
      });
      const res = await fetch(`${API_BASE}/route-finder?${params.toString()}`);

      if (res.status === 404) {
        setResult({ found: false });
        return;
      }
      if (!res.ok) {
        setError("Something went wrong. Try again.");
        return;
      }

      const data = await res.json();
      setResult({ found: true, ...data });
    } catch {
      setError("Couldn't reach the server. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  // Only meaningful if every leg has road geometry (OSRM succeeded for all of them).
  const totalDurationS =
    result?.found && result.legs.every((leg) => leg.road_geometry)
      ? result.legs.reduce((sum, leg) => sum + (leg.road_geometry?.duration_s ?? 0), 0)
      : null;

  return (
    <main className="flex h-screen w-screen flex-col md:flex-row">
      <aside className="flex w-full flex-col gap-4 overflow-y-auto border-b border-route-line p-4 md:h-full md:max-w-sm md:border-b-0 md:border-r">
        <div>
          <h1 className="text-lg font-semibold">Kathmandu Bus Route Finder</h1>
          <p className="text-sm text-neutral-400">
            Find a direct or single-transfer bus route across the Valley.
          </p>
        </div>

        <SearchForm
          stops={stops}
          stopsLoading={stopsLoading}
          apiBase={API_BASE}
          onSearch={handleSearch}
          loading={loading}
        />

        {stopsError && (
          <p className="rounded-md border border-amber-900 bg-amber-950/40 px-3 py-2 text-sm text-amber-300">
            Couldn&apos;t load the stop list from the server. You can still search if you know
            exact stop names, but suggestions won&apos;t be available.
          </p>
        )}

        <div aria-live="polite" className="flex flex-col gap-2">
          {error && (
            <p className="rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-400">
              {error}
            </p>
          )}

          {result && !result.found && (
            <p className="rounded-md bg-route-panel px-3 py-2 text-sm text-neutral-300">
              No direct or single-transfer route found between those stops.
            </p>
          )}

          {result && result.found && (
            <div className="flex flex-col gap-2 text-sm">
              <p className="text-neutral-400">
                {result.transfer_count === 0
                  ? "Direct route"
                  : `${result.transfer_count} transfer${result.transfer_count > 1 ? "s" : ""}`}
                {" · "}
                {(result.total_cost / 1000).toFixed(1)} km
                {totalDurationS !== null && <> · ~{formatDuration(totalDurationS)}</>}
              </p>
              {result.legs.map((leg, i) => {
                const isWalk = leg.route_id === "TRANSFER";
                return (
                  <div
                    key={`${leg.route_id}-${i}`}
                    className="flex items-start gap-2 rounded-md bg-route-panel px-3 py-2"
                  >
                    <span
                      className="mt-0.5 h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{
                        backgroundColor: isWalk
                          ? "#9CA3AF"
                          : LEG_COLORS[i % LEG_COLORS.length],
                      }}
                      aria-hidden
                    />
                    <div>
                      <p className="font-medium">{leg.route_name}</p>
                      <p className="text-neutral-400">
                        {leg.board_stop.stop_name} → {leg.alight_stop.stop_name}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {!result && !error && (
            <p className="text-sm text-neutral-500">
              Pick a starting stop and a destination, then hit Find route to see it on the map.
            </p>
          )}
        </div>
      </aside>

      <div className="min-h-[50vh] flex-1 md:min-h-0">
        <BusMap key="bus-map" result={result} />
      </div>
    </main>
  );
}

// Kept in sync with LEG_COLORS in components/BusMap.tsx so the legend in
// the sidebar matches the polylines drawn on the map.
const LEG_COLORS = ["#3DDC97", "#F2A93B", "#5DA9E9", "#E06C75"];