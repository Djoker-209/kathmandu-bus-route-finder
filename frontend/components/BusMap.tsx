"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import { RouteSearchResult } from "@/types/route";

const VALLEY_CENTER: [number, number] = [27.7041, 85.32];

const LEG_COLORS = ["#3DDC97", "#F2A93B", "#5DA9E9", "#E06C75"];

const busIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

interface BusMapProps {
  result?: RouteSearchResult | null;
}

export default function BusMap({ result }: BusMapProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return;
    }

    const map = L.map(mapContainerRef.current).setView(VALLEY_CENTER, 12);
    mapRef.current = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const routeLayer = L.layerGroup().addTo(map);

    if (result?.found) {
      const bounds: L.LatLngExpression[] = [];

      result.legs.forEach((leg, i) => {
        const fromMarker = L.marker(
          [leg.board_stop.lat, leg.board_stop.lng],
          { icon: busIcon }
        );
        fromMarker.bindPopup(leg.board_stop.stop_name);
        routeLayer.addLayer(fromMarker);

        const toMarker = L.marker(
          [leg.alight_stop.lat, leg.alight_stop.lng],
          { icon: busIcon }
        );
        toMarker.bindPopup(leg.alight_stop.stop_name);
        routeLayer.addLayer(toMarker);

        // Small dot for every intermediate stop (skip first/last — those
        // already have the full bus-icon marker above).
        leg.stops.slice(1, -1).forEach((stop) => {
          const dot = L.circleMarker([stop.lat, stop.lng], {
            radius: 5,
            color: LEG_COLORS[i % LEG_COLORS.length],
            fillColor: "#ffffff",
            fillOpacity: 1,
            weight: 2,
          });
          dot.bindPopup(stop.stop_name);
          routeLayer.addLayer(dot);
        });

        // GeoJSON coordinates are [lng, lat]; Leaflet wants [lat, lng].
        const roadPoints = leg.road_geometry?.geometry.coordinates.map(
          ([lng, lat]) => [lat, lng] as [number, number]
        );

        // Falls back to a straight line only if OSRM failed for this leg
        // (see backend _attach_road_geometry's `except OSRMError: pass`).
        const points: [number, number][] =
          roadPoints ?? [
            [leg.board_stop.lat, leg.board_stop.lng],
            [leg.alight_stop.lat, leg.alight_stop.lng],
          ];

        const polyline = L.polyline(points, {
          color: LEG_COLORS[i % LEG_COLORS.length],
          weight: 5,
        });
        routeLayer.addLayer(polyline);

        bounds.push(...points);
      });

      if (bounds.length > 0) {
        map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40] });
      }
    }

    return () => {
      routeLayer.remove();
    };
  }, [result]);

  return (
    <div
      ref={mapContainerRef}
      style={{ height: "100%", width: "100%", minHeight: "500px" }}
    />
  );
}