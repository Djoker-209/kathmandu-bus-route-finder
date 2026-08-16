"use client";

import { useState } from "react";
import { Stop } from "@/types/route";

interface SearchFormProps {
  stops: Stop[];
  onSearch: (originId: string, destinationId: string) => void;
  loading?: boolean;
}

export default function SearchForm({ stops, onSearch, loading }: SearchFormProps) {
  const [originText, setOriginText] = useState("");
  const [destinationText, setDestinationText] = useState("");

  function resolveStopId(typedName: string): string | null {
    const match = stops.find(
      (s) => s.stop_name.trim().toLowerCase() === typedName.trim().toLowerCase()
    );
    return match?.stop_id ?? null;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const originId = resolveStopId(originText);
    const destinationId = resolveStopId(destinationText);

    if (!originId || !destinationId) {
      // TODO: surface a proper inline error instead of a native alert
      // once the stop list is confirmed working end-to-end.
      alert("Please pick a valid stop from the suggestions for both fields.");
      return;
    }

    onSearch(originId, destinationId);
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
          value={originText}
          onChange={(e) => setOriginText(e.target.value)}
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
          value={destinationText}
          onChange={(e) => setDestinationText(e.target.value)}
          placeholder="Destination stop"
          className="rounded-md bg-route-bg border border-route-line px-3 py-2 text-sm outline-none focus:border-route-accent"
        />
      </div>

      {/* Fine for small stop counts. If the full stop list is large,
          swap this for a debounced /stops?search= call instead. */}
      <datalist id="stop-options">
        {stops.map((s) => (
          <option key={s.stop_id} value={s.stop_name} />
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
