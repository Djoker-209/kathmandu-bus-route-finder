"""Generates new primary-key IDs for stops/routes created via the admin
API. Existing IDs come from an external pipeline (stops: S#### convention;
routes: OSM-derived R-numbers, not sequential/owned by this app) -- see
migrations/versions/0002_replace_with_full_schema.py.

Stops: next sequential number in the existing S#### convention.
Routes: a separate M###### prefix, reserved for admin-created routes only,
so a manually created route can never collide with a future OSM-sourced
R-numbered import.

Not race-safe under concurrent creates (two simultaneous requests could
compute the same next ID) -- acceptable for a small internal admin tool;
revisit with a DB sequence or advisory lock if this ever needs concurrent
writers.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session


def next_stop_id(db: Session) -> str:
    next_n = db.execute(
        text(
            "SELECT COALESCE(MAX(CAST(SUBSTRING(stop_id FROM 2) AS INTEGER)), 0) + 1 "
            "FROM stops WHERE stop_id ~ '^S[0-9]+$'"
        )
    ).scalar_one()
    return f"S{next_n:04d}"


def next_route_id(db: Session) -> str:
    next_n = db.execute(
        text(
            "SELECT COALESCE(MAX(CAST(SUBSTRING(route_id FROM 2) AS INTEGER)), 0) + 1 "
            "FROM routes WHERE route_id ~ '^M[0-9]+$'"
        )
    ).scalar_one()
    return f"M{next_n:06d}"
