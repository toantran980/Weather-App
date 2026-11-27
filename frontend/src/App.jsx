// Tran, Toan
// Weather API Fullstack Web App PM Accelerator Assessment

import { useState } from "react";
import SavedSearches from "./components/SavedSearches";
import WeatherResults from "./components/WeatherResults";

async function api(url, options) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new Error("Cannot reach the backend. Start it with `python app.py` in the backend folder.");
  }
  const body = response.status === 204 ? {} : await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || "Something went wrong. Try again.");
  return body;
}


const jsonRequest = (method, body) => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});


function formatTemperature(celsius, fahrenheit) {
  return `${Math.round(fahrenheit ? (celsius * 9) / 5 + 32 : celsius)}°${fahrenheit ? "F" : "C"}`;
}


export default function App() {
  const [query, setQuery] = useState("");
  const [place, setPlace] = useState("");
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fahrenheit, setFahrenheit] = useState(false);

  async function searchLocation(location) {
    setLoading(true);
    setError("");
    try {
      const result = await api(`/api/weather?location=${encodeURIComponent(location)}`);
      setWeather(result);
      setPlace(location);
    } catch (requestError) {
      setWeather(null);
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  function submitSearch(event) {
    event.preventDefault();
    const location = query.trim();
    if (!location) {
      setError("Please enter a location.");
      return;
    }
    searchLocation(location);
  }

  function searchMyLocation() {
    if (!navigator.geolocation) {
      setError("Geolocation isn't supported by this browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => searchLocation(`${coords.latitude.toFixed(4)},${coords.longitude.toFixed(4)}`),
      () => setError("Location access was denied. Type a location instead.")
    );
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand-mark" aria-hidden="true">☁</div>
        <div>
          <p className="eyebrow">YOUR LOCAL FORECAST</p>
          <h1>Weather, wherever you are.</h1>
          <p className="intro">A little more sunshine in your day starts with a forecast.</p>
        </div>
      </header>

      <form onSubmit={submitSearch} className="search-panel">
        <label className="search-field">
          <span aria-hidden="true">⌕</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Location"
            placeholder="City, zip code, landmark or lat,lon" />
        </label>
        <button className="button button-primary" type="submit">Search</button>
        <button className="button button-secondary" type="button" onClick={searchMyLocation}><span aria-hidden="true">◎</span> Use my location</button>
        <button className="unit-toggle" type="button" onClick={() => setFahrenheit(!fahrenheit)}
          aria-label={`Switch to degrees ${fahrenheit ? "Celsius" : "Fahrenheit"}`}>
          °{fahrenheit ? "C" : "F"}
        </button>
      </form>

      {loading && <p role="status">Loading…</p>}
      {error && <p className="error-banner" role="alert"><span aria-hidden="true">!</span>{error}</p>}
      <WeatherResults data={weather} fahrenheit={fahrenheit} formatTemperature={formatTemperature} />
      <SavedSearches place={place} locationName={weather?.location.name} fahrenheit={fahrenheit}
        api={api} jsonRequest={jsonRequest} formatTemperature={formatTemperature} />

      <footer className="app-footer">
        Built by Toan Tran. PM Accelerator is a US-based company with a global reach, premiering in AI learning and as a development hub, featuring award-winning AI products and mentors from top-tier companies such as Google, Meta, Apple, and Nvidia. It offers a dynamic AI PM Bootcamp, designed to empower the next generation of AI professionals through hands-on experience, mentorship, and real-world projects. Website: https://www.pmaccelerator.io/
      </footer>
    </main>
  );
}
