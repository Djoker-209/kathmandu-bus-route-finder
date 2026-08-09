"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import SearchForm from "@/components/SearchForm";
import { getMockStops, getMockRouteResult, getMockNoRouteResult } from "@/lib/mockRoute";
import { RouteSearchResult } from "@/types/route";

// Leaflet touches `window`, so the map must load client-side only.
const BusMap = dynamic(() => import("@/components/BusMap"), { ssr: false });

const stops = getMockStops();

export default function Home() {
  const [result, setResult] = useState<RouteSearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(originId: string, destinationId: string) {
    setLoading(true);
    setError(null);

    // --- MOCK BLOCK: replace this whole block with a real fetch once the
    // backend is live, e.g.:
    //
    // const res = await fetch("/api/route/search", {
    //   method: "POST",
    //   headers: { "Content-Type": "application/json" },
    //   body: JSON.stringify({ origin: originId, destination: destinationId }),
    // });
    // if (!res.ok) { setError("Something went wrong. Try again."); setLoading(false); return; }
    // const data: RouteSearchResult = await res.json();
    try {
      await new Promise((r) => setTimeout(r, 400)); // simulate network latency
      const sameStop = originId.trim().toLowerCase() === destinationId.trim().toLowerCase();
      const data = sameStop ? getMockNoRouteResult() : getMockRouteResult();
      setResult(data);
    } catch {
      setError("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
    // --- END MOCK BLOCK
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
              {result.total_distance_km ? ` · ${result.total_distance_km} km` : ""}
            </p>
            {result.legs.map((leg) => (
              <div key={leg.route_id} className="bg-route-panel rounded-md px-3 py-2">
                <p className="font-medium">{leg.route_name}</p>
                <p className="text-neutral-400">
                  {leg.from_stop.name} → {leg.to_stop.name}
                </p>
              </div>
            ))}
          </div>
        )}
      </aside>

      <div className="flex-1">
        <BusMap result={result} />
      </div>
    </main>
  );
}
