# Weather App

Full-stack weather app for the PM Accelerator Tech Assessments 1 and 2. Built by Toan Tran with a React/Vite frontend and a FastAPI/SQLite backend.

## Features

- Search by city, postal code, landmark, address, GPS coordinates, or browser location.
- Current weather and a five-day forecast with a Celsius/Fahrenheit toggle.
- Current U.S. air-quality index, PM2.5, and PM10 when data is available.
- YouTube travel-video results when an API key is configured; a YouTube search link is available without a key.
- Location summary and OpenStreetMap link.
- Save, list, edit, delete, and export searches. CSV and JSON exports are supported.
- Responsive layout and error messages for invalid locations, denied geolocation, and service failures.

## Project layout

```text
backend/
  app.py          FastAPI routes, request models, and app startup
  settings.py     Environment loading, shared settings, and API errors
  database.py     SQLite access helpers
  services.py     Geocoding and external weather integrations
  tests/          Backend tests
frontend/src/
  App.jsx                 Search flow and page layout
  components/             Weather results and saved searches
.example.env              Example environment variables
```

## Setup

### Optional YouTube API key

Weather and air-quality data don’t need API keys. To get YouTube video results, create a YouTube Data API v3 key and add it to the project-root `.env` file.

Copy `.example.env` to `.env`:

```powershell
Copy-Item .example.env .env
```

Or, on Linux:

```bash
cp .example.env .env
```

Set `YOUTUBE_API_KEY` in `.env`. The backend loads this file on startup. Keep `.env` private; it is ignored by Git. Without a key, the app still offers a direct YouTube search link.

### Start the backend

In a terminal:

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The API runs at `http://127.0.0.1:5000`. Interactive API docs are at `http://127.0.0.1:5000/docs`.

### Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite forwards `/api` requests to the backend at `http://127.0.0.1:5000`, so start the backend first.

## API overview

| Method     | Endpoint                      | Purpose                                                      |
| ---------- | ----------------------------- | ------------------------------------------------------------ |
| `GET`    | `/api/weather?location=...` | Current weather, forecast, air quality, and location details |
| `POST`   | `/api/searches`             | Save a location and date range                               |
| `GET`    | `/api/searches`             | List saved searches; optional `?q=` filter                 |
| `GET`    | `/api/searches/{id}`        | Read one saved search                                        |
| `PUT`    | `/api/searches/{id}`        | Update a saved search                                        |
| `DELETE` | `/api/searches/{id}`        | Delete a saved search                                        |
| `GET`    | `/api/export?format=csv`    | Download saved daily weather as CSV                          |
| `GET`    | `/api/export?format=json`   | Download saved searches as JSON                              |

Date ranges are validated, and locations are resolved through Open-Meteo Geocoding with Nominatim as a fallback. Saved weather data is stored in SQLite.

## Tests

Backend tests use mocked external API responses:

```bash
cd backend
pytest
```

## About PM Accelerator

PM Accelerator is a US-based company with a global reach, premiering in AI learning and as a development hub, featuring award-winning AI products and mentors from top-tier companies such as Google, Meta, Apple, and Nvidia. It offers a dynamic AI PM Bootcamp, designed to empower the next generation of AI professionals through hands-on experience, mentorship, and real-world projects. Website: https://www.pmaccelerator.io
