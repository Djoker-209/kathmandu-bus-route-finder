# this will be my folder structure

backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── stops.py
│   │   ├── admin.py
│   │   └── schemas.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   ├── graph_loader.py
│   │   └── schema.sql
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py
│   │
│   ├── graph_engine/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── models.py
│   │   ├── utils.py
│   │   ├── sample_data.py
│   │   ├── graph_builder.py
│   │   ├── route_finder.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_utils.py
│   │       ├── test_graph_builder.py
│   │       ├── test_route_finder.py
│   │       ├── test_sample_data.py
│   │       └── test_integration.py
│   │
│   ├── __init__.py
│   └── main.py
│
├── migrations/
├── tests/
├── .env.example
├── alembic.ini
├── Dockerfile
└── requirements.txt