#!/bin/bash
export PYTHONPATH=/app/src
alembic upgrade head && uvicorn pharmatrack.main:app --host 0.0.0.0 --port $PORT
```

Y en Railway cambiar el Start Command a:
```
bash start.sh