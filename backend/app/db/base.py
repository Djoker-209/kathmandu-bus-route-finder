"""Single import point that pulls in `Base` plus every ORM model.

Alembic's `migrations/env.py` imports `Base` for autogenerate support
(`alembic revision --autogenerate`). That only picks up models that
have actually been imported somewhere by the time `Base.metadata` is
read, so this module exists purely for its import side-effects --
importing it registers Stop/Route/RouteStop on `Base.metadata`.
"""

from app.models import Base, Route, RouteStop, Stop  # noqa: F401
