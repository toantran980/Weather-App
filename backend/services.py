# Geocoding and weather data integrations used by the API routes.

import functools
import logging
import os
from datetime import date, timedelta
from urllib.parse import quote, urlencode

import requests

from settings import ApiError, REQUEST_HEADERS, WEATHER_CONDITIONS


def get_json(request_url, **query_params):
    try:
        response = requests.get(request_url, params=query_params, headers=REQUEST_HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        error_details = str(exc)
        for credential_name in ("key", "api_key", "apikey"):
            credential = query_params.get(credential_name)
            if credential:
                error_details = error_details.replace(str(credential), "[redacted]")
        logging.getLogger(__name__).warning("Upstream request failed (%s): %s", request_url, error_details)
        raise ApiError("The weather or location service is unavailable. Try again shortly.", 502)


@functools.lru_cache(maxsize=256)
def geocode(query_text):
    query_text = str(query_text or "").strip()
    if not query_text:
        raise ApiError("Please enter a location.")
    coordinate_parts = query_text.split(",")
    if len(coordinate_parts) == 2:
        try:
            latitude, longitude = (float(part.strip()) for part in coordinate_parts)
        except ValueError:
            pass
        else:
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ApiError("Coordinates are out of range.")
            return {
                "name": f"{latitude:.4f}, {longitude:.4f}",
                "lat": latitude,
                "lon": longitude,
            }
    geocoding_results = get_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        name=query_text,
        count=1,
    ).get("results")
    if geocoding_results:
        result = geocoding_results[0]
        display_name = ", ".join(filter(None, [result["name"], result.get("admin1"), result.get("country")]))
        return {"name": display_name, "lat": result["latitude"], "lon": result["longitude"]}
    address_results = get_json(
        "https://nominatim.openstreetmap.org/search",
        q=query_text,
        format="json",
        limit=1,
    )
    if address_results:
        result = address_results[0]
        return {"name": result["display_name"], "lat": float(result["lat"]), "lon": float(result["lon"])}
    raise ApiError(
        f"Could not find a location matching '{query_text}'. Check the spelling or try a nearby city.",
        404,
    )


def optional(integration, *args):
    try:
        return integration(*args)
    except Exception:
        return None


def wiki_summary(location_data):
    title = location_data["name"].split(",")[0].strip()
    try:
        float(title)
    except ValueError:
        pass
    else:
        return None
    return get_json("https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(title)).get("extract")


def air_quality(location_data):
    data = get_json("https://air-quality-api.open-meteo.com/v1/air-quality",
                    latitude=location_data["lat"], longitude=location_data["lon"],
                    current="us_aqi,pm2_5,pm10", timezone="auto")
    current = data.get("current", {})
    index = current.get("us_aqi")
    if index is None:
        category = "Unavailable"
    elif index <= 50:
        category = "Good"
    elif index <= 100:
        category = "Moderate"
    elif index <= 150:
        category = "Unhealthy for sensitive groups"
    elif index <= 200:
        category = "Unhealthy"
    elif index <= 300:
        category = "Very unhealthy"
    else:
        category = "Hazardous"
    return {
        "us_aqi": index,
        "category": category,
        "pm2_5": current.get("pm2_5"),
        "pm10": current.get("pm10"),
        "time": current.get("time"),
    }


def youtube_videos(location_data):
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        return []
    results = get_json(
        "https://www.googleapis.com/youtube/v3/search",
        part="snippet",
        q=location_data["name"] + " travel",
        maxResults=3,
        type="video",
        key=api_key,
    ).get("items", [])
    return [
        {
            "title": item["snippet"]["title"],
            "url": "https://www.youtube.com/watch?v=" + item["id"]["videoId"],
        }
        for item in results
        if item.get("id", {}).get("videoId")
    ]


def youtube_search_url(location_data):
    return "https://www.youtube.com/results?" + urlencode({"search_query": location_data["name"] + " travel"})


def map_info(location_data):
    latitude, longitude = location_data["lat"], location_data["lon"]
    map_url = (
        f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}"
        f"#map=11/{latitude}/{longitude}"
    )
    return {"map_link": map_url}


def current_weather(location_data):
    data = get_json(
        "https://api.open-meteo.com/v1/forecast",
        latitude=location_data["lat"],
        longitude=location_data["lon"],
        current="temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
        daily="temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
        forecast_days=5,
        timezone="auto",
    )
    current, daily = data["current"], data["daily"]
    rain_chances = daily.get("precipitation_probability_max") or [None] * len(daily["time"])
    forecast = []
    for day, high, low, code, rain_chance in zip(
        daily["time"],
        daily["temperature_2m_max"],
        daily["temperature_2m_min"],
        daily["weather_code"],
        rain_chances,
    ):
        forecast.append(
            {
                "date": day,
                "max_c": high,
                "min_c": low,
                "conditions": WEATHER_CONDITIONS.get(code, "Unknown"),
                "code": code,
                "rain_pct": rain_chance,
            }
        )

    return {
        "temp_c": current["temperature_2m"],
        "feels_like_c": current["apparent_temperature"],
        "humidity_pct": current["relative_humidity_2m"],
        "wind_kmh": current["wind_speed_10m"],
        "conditions": WEATHER_CONDITIONS.get(current["weather_code"], "Unknown"),
        "code": current["weather_code"],
        "forecast": forecast,
    }


def check_dates(start_date, end_date):
    today = date.today()
    if start_date > end_date:
        raise ApiError("Start date must be on or before the end date.")
    if (end_date - start_date).days > 30:
        raise ApiError("Date range can be at most 31 days.")
    if start_date < date(1940, 1, 1) or end_date > today + timedelta(days=15):
        raise ApiError("Dates must be between 1940 and 15 days from today.")
    if end_date >= today - timedelta(days=5) and start_date < today - timedelta(days=90):
        raise ApiError("Ranges that include the last 5 days must start within the last 90 days.")


def daily_temps(location_data, start_date, end_date):
    archive = end_date < date.today() - timedelta(days=5)
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        if archive
        else "https://api.open-meteo.com/v1/forecast"
    )
    daily = get_json(
        url,
        latitude=location_data["lat"],
        longitude=location_data["lon"],
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        daily="temperature_2m_max,temperature_2m_min,precipitation_sum",
        timezone="auto",
    )["daily"]
    precipitation = daily.get("precipitation_sum") or [None] * len(daily["time"])
    return [
        {"date": day, "max_c": high, "min_c": low, "precip_mm": rain}
        for day, high, low, rain in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            precipitation,
        )
    ]
