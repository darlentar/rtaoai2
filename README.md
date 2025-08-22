# rtaoai2

This project uses [uv](https://docs.astral.sh/uv/)
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
