# rtaoai2


This project uses [uv](https://docs.astral.sh/uv/) and requires Python >=3.13 (as declared in `pyproject.toml`).
To run it

Run the backend
````
uv sync
uv run pytest
OPENAI_API_KEY=$(cat ~/.you_openai_key) uv run fastapi dev src/rtaoai2/server.py
````

Run the frontend
````
cd react-ui
npm start
````
