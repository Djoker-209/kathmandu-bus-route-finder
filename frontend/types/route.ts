// Mirrors backend/app/schemas.py exactly. Keep in sync if the backend changes.

export interface Stop {
  stop_id: string;
  stop_name: string;
  lat: number;
  lng: number;
  zone?: string | null;
  district?: string | null;
  is_major_stop: boolean;
  is_interchange: boolean;
  status: string;
}

export interface RoadGeometry {
  // GeoJSON LineString: coordinates are [lng, lat] pairs, per GeoJSON spec.
  // Convert to [lat, lng] before handing to Leaflet.
  geometry: {
    type: "LineString";
    coordinates: [number, number][];
  };
  distance_m: number;
  duration_s: number;
}

export interface RouteLeg {
  route_id: string;
  route_name: string;
  board_stop: Stop;
  alight_stop: Stop;
  num_stops: number;
  stops: Stop[]; // every physical stop on this leg, in order, board→alight inclusive
  road_geometry?: RoadGeometry | null;
}

export interface RouteFinderResult {
  origin_stop_id: string;
  destination_stop_id: string;
  total_cost: number;
  transfer_count: number;
  legs: RouteLeg[];
}

// Frontend-only wrapper: the backend signals "not found" via HTTP 404,
// not a `found` field, so we add it client-side after the fetch.
export type RouteSearchResult =
  | ({ found: true } & RouteFinderResult)
  | { found: false };