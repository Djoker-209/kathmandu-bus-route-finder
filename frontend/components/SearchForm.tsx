"use client";

import { useState } from "react";
import { Stop } from "@/types/route";

interface SearchFormProps {
  stops: Stop[];
  stopsLoading?: boolean;
  apiBase: string;
  onSearch: (originId: string, destinationId: string) => void;
  loading?: boolean;
}

type FieldError = "origin" | "destination" | "both" | null;

export default function SearchForm({
  stops,
  stopsLoading,
  apiBase,
  onSearch,
  loading,
}: SearchFormProps) {
  const [originText, setOriginText] = useState("");
  const [destinationText, setDestinationText] = useState("");
  const [fieldError, setFieldError] = useState<FieldError>(null);
  const [locating, setLocating] = useState(false);
  const [locateError, setLocateError] = useState<string | null>(null);

  function resolveStop(typedName: string): Stop | null {
    return (
      stops.find(
        (s) => s.stop_name.trim().toLowerCase() === typedName.trim().toLowerCase()
      ) ?? null
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const origin = resolveStop(originText);
    const destination = resolveStop(destinationText);

    if (!origin && !destination) {
      setFieldError("both");
      return;
    }
    if (!origin) {
      setFieldError("origin");
      return;
    }
    if (!destination) {
      setFieldError("destination");
      return;
    }
    if (origin.stop_id === destination.stop_id) {
      setFieldError("both");
      return;
    }

    setFieldError(null);
    onSearch(origin.stop_id, destination.stop_id);
  }

  function handleSwap() {
    setOriginText(destinationText);
    setDestinationText(originText);
    setFieldError(null);
  }

  function useMyLocation() {
    if (!navigator.geolocation) {
      setLocateError("Geolocation isn't available in this browser.");
      return;
    }

    setLocating(true);
    setLocateError(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const params = new URLSearchParams({
            lat: String(latitude),
            lng: String(longitude),
            limit: "1",
          });
          const res = await fetch(`${apiBase}/stops/nearby?${params.toString()}`);
          if (!res.ok) throw new Error();
          const nearby: Stop[] = await res.json();
          if (nearby.length === 0) {
            setLocateError("No stops found near your location.");
            return;
          }
          setOriginText(nearby[0].stop_name);
          setFieldError(null);
        } catch {
          setLocateError("Couldn't find a nearby stop. Try again.");
        } finally {
          setLocating(false);
        }
      },
      () => {
        setLocateError("Location permission denied.");
        setLocating(false);
      },
      { timeout: 8000 }
    );
  }

  const originInvalid = fieldError === "origin" || fieldError === "both";
  const destinationInvalid = fieldError === "destination" || fieldError === "both";

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 rounded-lg bg-route-panel p-4">
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between">
          <label htmlFor="origin" className="text-xs uppercase tracking-wide text-neutral-400">
            From
          </label>
          <button
            type="button"
            onClick={useMyLocation}
            disabled={locating}
            className="text-xs text-route-accent hover:underline disabled:opacity-50"
          >
            {locating ? "Locating…" : "Use my location"}
          </button>
        </div>
        <input
          id="origin"
          list="stop-options"
          value={originText}
          onChange={(e) => {
            setOriginText(e.target.value);
            if (fieldError) setFieldError(null);
          }}
          placeholder={stopsLoading ? "Loading stops…" : "Origin stop"}
          autoComplete="off"
          aria-invalid={originInvalid}
          className={`rounded-md border bg-route-bg px-3 py-2 text-sm outline-none focus:border-route-accent ${
            originInvalid ? "border-red-700" : "border-route-line"
          }`}
        />
      </div>

      <div className="-my-1 flex justify-center">
        <button
          type="button"
          onClick={handleSwap}
          aria-label="Swap origin and destination"
          title="Swap origin and destination"
          className="rounded-full border border-route-line bg-route-bg px-2 py-1 text-xs text-neutral-400 hover:border-route-accent hover:text-route-accent"
        >
          ↕ Swap
        </button>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="destination" className="text-xs uppercase tracking-wide text-neutral-400">
          To
        </label>
        <input
          id="destination"
          list="stop-options"
          value={destinationText}
          onChange={(e) => {
            setDestinationText(e.target.value);
            if (fieldError) setFieldError(null);
          }}
          placeholder={stopsLoading ? "Loading stops…" : "Destination stop"}
          autoComplete="off"
          aria-invalid={destinationInvalid}
          className={`rounded-md border bg-route-bg px-3 py-2 text-sm outline-none focus:border-route-accent ${
            destinationInvalid ? "border-red-700" : "border-route-line"
          }`}
        />
      </div>

      {/* Fine for small stop counts. If the full stop list is large,
          swap this for a debounced /stops?search= call instead. */}
      <datalist id="stop-options">
        {stops.map((s) => (
          <option key={s.stop_id} value={s.stop_name} />
        ))}
      </datalist>

      {fieldError && (
        <p className="text-xs text-red-400" role="alert">
          {fieldError === "both" && originText.trim() && originText === destinationText
            ? "Origin and destination can't be the same stop."
            : "Pick a valid stop from the suggestions for both fields."}
        </p>
      )}
      {locateError && (
        <p className="text-xs text-red-400" role="alert">
          {locateError}
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="mt-1 rounded-md bg-route-accent py-2 text-sm font-medium text-route-bg disabled:opacity-50"
      >
        {loading ? "Searching…" : "Find route"}
      </button>
    </form>
  );
}
