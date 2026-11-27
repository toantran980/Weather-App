const WEATHER_ICONS = {
  0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️",
  51: "🌦️", 53: "🌦️", 55: "🌦️", 61: "🌧️", 63: "🌧️", 65: "🌧️",
  71: "🌨️", 73: "🌨️", 75: "❄️", 80: "🌦️", 81: "🌧️", 82: "⛈️",
  95: "⛈️", 96: "⛈️", 99: "⛈️",
};

const weatherIcon = (code) => WEATHER_ICONS[code] || "❓";
const formatDay = (date) => new Date(`${date}T00:00`).toLocaleDateString(undefined, {
  weekday: "short", month: "short", day: "numeric",
});


function aqiClass(value) {
  if (value == null) return "aqi-unavailable";
  if (value <= 50) return "aqi-good";
  if (value <= 100) return "aqi-moderate";
  if (value <= 150) return "aqi-sensitive";
  if (value <= 200) return "aqi-unhealthy";
  if (value <= 300) return "aqi-very-unhealthy";
  return "aqi-hazardous";
}


export default function WeatherResults({ data, fahrenheit, formatTemperature }) {
  if (!data) return null;
  const current = data.current;
  const temperature = (value) => formatTemperature(value, fahrenheit);
  const placeName = data.location.name.split(",")[0];

  return (
    <div className="weather-content">
      <section className="current-card">
        <div className="current-copy">
          <p className="eyebrow">CURRENT CONDITIONS</p>
          <h2>{data.location.name}</h2>
          <p className="condition-label">{current.conditions}</p>
          <a className="map-link" href={data.map_link} target="_blank" rel="noreferrer">View location on map <span aria-hidden="true">↗</span></a>
        </div>
        <div className="current-temp" aria-label={`${temperature(current.temp_c)}, ${current.conditions}`}>
          <span className="current-icon" aria-hidden="true">{weatherIcon(current.code)}</span>
          <span className="big">{temperature(current.temp_c)}</span>
        </div>
        <div className="weather-details">
          <div><span>Feels like</span><strong>{temperature(current.feels_like_c)}</strong></div>
          <div><span>Humidity</span><strong>{current.humidity_pct}%</strong></div>
          <div><span>Wind</span><strong>{current.wind_kmh} <small>km/h</small></strong></div>
        </div>
      </section>

      <section className="forecast-section">
        <div className="section-heading">
          <div><p className="eyebrow">PLAN AHEAD</p><h2>5-day forecast</h2></div>
          <span className="section-note">Daily high / low</span>
        </div>
        <div className="forecast-grid">
          {current.forecast.map((forecastDay) => (
            <div className="forecast-card" key={forecastDay.date}>
              <strong className="forecast-day">{formatDay(forecastDay.date)}</strong>
              <div className="icon" aria-hidden="true">{weatherIcon(forecastDay.code)}</div>
              <div className="forecast-temps"><strong>{temperature(forecastDay.max_c)}</strong><span>{temperature(forecastDay.min_c)}</span></div>
              <small className="forecast-condition">{forecastDay.conditions}</small>
              <small className="rain-chance">{forecastDay.rain_pct == null ? "Rain chance unavailable" : `☂ ${forecastDay.rain_pct}% chance of rain`}</small>
            </div>
          ))}
        </div>
      </section>

      {(data.about || data.air_quality || data.videos?.length > 0 || data.youtube_search_url) && (
        <section className="extras" aria-label="More about this location">
          {data.about && <article className="card"><h3>About {placeName}</h3><p>{data.about}</p></article>}
          {data.air_quality && (
            <article className="card air-quality-card">
              <div className="air-quality-header">
                <div><p className="eyebrow">AIR QUALITY</p><h3>Current conditions</h3></div>
                {data.air_quality.us_aqi != null && <div className={`aqi-badge ${aqiClass(data.air_quality.us_aqi)}`}>
                  <strong>{data.air_quality.us_aqi}</strong><span>US AQI · {data.air_quality.category}</span>
                </div>}
              </div>
              {data.air_quality.us_aqi == null && <p>Air quality index is unavailable for this location.</p>}
              <div className="pollutant-grid">
                <div><span>PM2.5</span><strong>{data.air_quality.pm2_5 == null ? "—" : `${data.air_quality.pm2_5} μg/m³`}</strong></div>
                <div><span>PM10</span><strong>{data.air_quality.pm10 == null ? "—" : `${data.air_quality.pm10} μg/m³`}</strong></div>
              </div>
              <p className="source-attribution">Estimates by <a href="https://open-meteo.com/en/docs/air-quality-api" target="_blank" rel="noreferrer">Open-Meteo</a>, using Copernicus CAMS ENSEMBLE data.</p>
            </article>
          )}
          {(data.videos?.length > 0 || data.youtube_search_url) && (
            <article className="card">
              <p className="eyebrow">EXPLORE THE AREA</p><h3>YouTube videos about {placeName}</h3>
              {data.videos?.length > 0 ? <ul className="video-list">{data.videos.map((video) => (
                <li key={video.url}><a href={video.url} target="_blank" rel="noreferrer">{video.title}</a></li>
              ))}</ul> : <p>Browse travel videos for this location on <a href={data.youtube_search_url} target="_blank" rel="noreferrer">YouTube</a>.</p>}
            </article>
          )}
        </section>
      )}
    </div>
  );
}
