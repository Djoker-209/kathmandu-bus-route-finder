// Shapes here are a proposed contract for /route/search — confirm the exact
// field names with Janak/Dipesh before backend work starts, then update this
// file to match their Pydantic schemas exactly.

export interface Stop {
  id: string;
  name: string;
  lat: number;
  lng: number;
}

export interface RouteLeg {
  route_id: string;
  route_name: string;
  from_stop: Stop;
  to_stop: Stop;
  // Ordered polyline points for this leg (straight-line stop sequence;
  // OSRM will later replace this with a road-following path).
  path: [number, number][]; // [lat, lng][]
}

export interface RouteSearchResult {
  found: boolean;
  transfer_count: number; // 0 = direct, 1 = single transfer
  total_distance_km?: number;
  legs: RouteLeg[];
}

export interface RouteSearchRequest {
  origin: string; // stop id or free-text, TBD with backend
  destination: string;
}
