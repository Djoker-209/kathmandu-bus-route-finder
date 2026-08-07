"""
sample_data.py

A miniature Kathmandu network that stands in for the database until
BRF-6 (real data collection) is done. Coordinates below are verified
via web search against real-world sources, not guessed -- this matters
because a wrong coordinate silently produces a wrong distance, which
silently produces a wrong route.

Network:

  Route 1 "Ratnapark - Tripureshwor" (the example corridor):
      Ratnapark -> New Road -> Tripureshwor

  Route 2 "Tripureshwor - Kalanki":
      Tripureshwor -> Kalanki

  Tripureshwor is a real, well-known interchange point in Kathmandu
  (it sits on the Ring Road), so it's used here deliberately -- Route 1
  and Route 2 each have their OWN "Tripureshwor" stop row, about 40m
  apart, exactly like two different operators' independently-collected
  stop pins for the same real place. This is what tests whether the
  proximity-based interchange detection actually works, not just
  whether the code runs.

  Budhanilkantha is included as a deliberately disconnected stop, for
  the "no route exists" edge case.
"""
"""Compact sample network for tests and demos."""

from .models import RouteStop, Stop


STOPS = [
    # --- Route 1: Ratnapark -> New Road -> Tripureshwor ---
    Stop(1, "Ratnapark", 27.7075, 85.3155),
    Stop(2, "New Road", 27.7020, 85.3074),
    Stop(3, "Tripureshwor (Rt.1 stop)", 27.6953, 85.3130),

    # --- Route 2: Tripureshwor -> Kalanki ---
    # Same real-world location as stop 3, ~40m away.
    Stop(4, "Tripureshwor (Rt.2 stop)", 27.6950, 85.3128),
    Stop(5, "Kalanki", 27.6939, 85.2803),  # approx, intermediate/endpoint

    # --- Deliberately disconnected ---
    Stop(99, "Budhanilkantha", 27.7807, 85.3617),
]


ROUTE_STOPS = [
    RouteStop(route_id=1, stop_id=1, sequence_order=1),
    RouteStop(route_id=1, stop_id=2, sequence_order=2),
    RouteStop(route_id=1, stop_id=3, sequence_order=3),

    RouteStop(route_id=2, stop_id=4, sequence_order=1),
    RouteStop(route_id=2, stop_id=5, sequence_order=2),
]

