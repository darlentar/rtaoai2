# rtaoai2

This project uses [rye](https://rye.astral.sh)
To run it

Run the backend
````
rye sync
rye run pytest
OPENAI_API_KEY=$(cat ~/.you_openai_key) rye run fastapi dev src/rtaoai2/server.py
````

Run the frontend
````
cd react-ui
npm start
````
