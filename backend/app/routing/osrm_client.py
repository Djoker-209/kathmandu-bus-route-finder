import os
import requests

OSRM_BASE_URL = os.environ.get("OSRM_BASE_URL", "http://localhost:5000")


class OSRMError(Exception):
    pass


def get_route_geometry(coords: list[tuple[float, float]], profile: str = "driving") -> dict:
    """coords: list of (lat, lon) in travel order, at least 2 points."""
    if len(coords) < 2:
        raise ValueError("Need at least 2 coordinates for OSRM routing")

    coord_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url = f"{OSRM_BASE_URL}/route/v1/{profile}/{coord_str}"
    params = {"overview": "full", "geometries": "geojson"}

    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise OSRMError(str(exc)) from exc

    data = resp.json()
    if data.get("code") != "Ok":
        raise OSRMError(f"OSRM returned code={data.get('code')}")

    route = data["routes"][0]
    return {
        "geometry": route["geometry"],   # GeoJSON LineString
        "distance_m": route["distance"],
        "duration_s": route["duration"],
    }