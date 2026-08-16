"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import SearchForm from "@/components/SearchForm";
import { RouteSearchResult, Stop } from "@/types/route";

// Leaflet touches `window`, so the map must load client-side only.
const BusMap = dynamic(() => import("@/components/BusMap"), { ssr: false });

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Home() {
  const [stops, setStops] = useState<Stop[]>([]);
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
          if (!res.ok) break;
          const data: { total: number; items: Stop[] } = await res.json();
          all.push(...data.items);
          offset += pageSize;
          if (offset >= data.total || data.items.length === 0) break;
        }

        setStops(all);
      } catch {
        // Non-fatal: the search form still works, just without suggestions.
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
      setError("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex h-screen w-screen">
      <aside className="w-full max-w-sm flex flex-col gap-4 p-4 overflow-y-auto border-r border-route-line">
        <div>
          <h1 className="text-lg font-semibold">Kathmandu Bus Route Finder</h1>
          <p className="text-sm text-neutral-400">
            Find a direct or single-transfer bus route across the Valley.
          </p>
        </div>

        <SearchForm stops={stops} onSearch={handleSearch} loading={loading} />

        {error && (
          <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-md px-3 py-2">
            {error}
          </p>
        )}

        {result && !result.found && (
          <p className="text-sm text-neutral-300 bg-route-panel rounded-md px-3 py-2">
            No direct or single-transfer route found between those stops.
          </p>
        )}

        {result && result.found && (
          <div className="flex flex-col gap-2 text-sm">
            <p className="text-neutral-400">
              {result.transfer_count === 0 ? "Direct route" : `${result.transfer_count} transfer`}
              {" · "}
              {(result.total_cost / 1000).toFixed(1)} km
            </p>
            {result.legs.map((leg, i) => (
              <div key={`${leg.route_id}-${i}`} className="bg-route-panel rounded-md px-3 py-2">
                <p className="font-medium">{leg.route_name}</p>
                <p className="text-neutral-400">
                  {leg.board_stop.stop_name} → {leg.alight_stop.stop_name}
                </p>
              </div>
            ))}
          </div>
        )}
      </aside>

      <div className="flex-1">
        <BusMap key="bus-map" result={result} />
      </div>
    </main>
  );
}