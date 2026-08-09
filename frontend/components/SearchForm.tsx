"use client";

import { useState } from "react";
import { Stop } from "@/types/route";

interface SearchFormProps {
  stops: Stop[];
  onSearch: (originId: string, destinationId: string) => void;
  loading?: boolean;
}

export default function SearchForm({ stops, onSearch, loading }: SearchFormProps) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!origin || !destination) return;
    onSearch(origin, destination);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 p-4 bg-route-panel rounded-lg">
      <div className="flex flex-col gap-1">
        <label htmlFor="origin" className="text-xs uppercase tracking-wide text-neutral-400">
          From
        </label>
        <input
          id="origin"
          list="stop-options"
          value={origin}
          onChange={(e) => setOrigin(e.target.value)}
          placeholder="Origin stop"
          className="rounded-md bg-route-bg border border-route-line px-3 py-2 text-sm outline-none focus:border-route-accent"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="destination" className="text-xs uppercase tracking-wide text-neutral-400">
          To
        </label>
        <input
          id="destination"
          list="stop-options"
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
          placeholder="Destination stop"
          className="rounded-md bg-route-bg border border-route-line px-3 py-2 text-sm outline-none focus:border-route-accent"
        />
      </div>

      {/* Real autocomplete (fuzzy match, /stops/nearest) replaces this datalist
          once the backend endpoint exists. */}
      <datalist id="stop-options">
        {stops.map((s) => (
          <option key={s.id} value={s.name} />
        ))}
      </datalist>

      <button
        type="submit"
        disabled={loading}
        className="mt-1 rounded-md bg-route-accent text-route-bg font-medium py-2 text-sm disabled:opacity-50"
      >
        {loading ? "Searching…" : "Find route"}
      </button>
    </form>
  );
}
