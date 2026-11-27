import app as m
import database
import settings
import services
import pytest
from fastapi.testclient import TestClient

def fake_get_json(url, **p):
    if "geocoding-api" in url:
        return {"results": [{"name": "Paris", "admin1": "Ile-de-France", "country": "France", "latitude": 48.85, "longitude": 2.35}]} if p["name"] == "Paris" else {}
    if "nominatim" in url:
        return []
    if "air-quality-api" in url:
        return {"current": {"us_aqi": 42, "pm2_5": 3.1, "pm10": 5.2}}
    if "youtube" in url:
        return {"items": [{"snippet": {"title": "Paris travel guide"}, "id": {"videoId": "video123"}}]}
    if "wikipedia" in url:
        return {"extract": "A city."}
    if "start_date" in p:
        return {"daily": {"time": [p["start_date"]], "temperature_2m_max": [20.0], "temperature_2m_min": [10.0], "precipitation_sum": [1.5]}}
    return {"current": {"temperature_2m": 15, "apparent_temperature": 14, "relative_humidity_2m": 60, "wind_speed_10m": 9, "weather_code": 1},
            "daily": {"time": ["2026-01-01"], "temperature_2m_max": [18], "temperature_2m_min": [9], "weather_code": [3]}}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(services, "get_json", fake_get_json)
    services.geocode.cache_clear()
    monkeypatch.setattr(settings, "DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")
    return TestClient(m.app)


def test_crud_and_export(client):
    body = {"location": "Paris", "start_date": "2026-01-01", "end_date": "2026-01-01", "note": "trip"}
    response = client.post("/api/searches", json=body)
    assert response.status_code == 201
    search_id = response.json()["id"]
    assert client.get(f"/api/searches/{search_id}").json()["name"].startswith("Paris")
    assert client.put(f"/api/searches/{search_id}", json={"note": "updated"}).json()["note"] == "updated"
    assert "Paris" in client.get("/api/export?format=csv").text
    assert client.get("/api/export?format=json").json()[0]["name"].startswith("Paris")
    assert client.get("/api/export?format=xml").status_code == 400
    assert client.delete(f"/api/searches/{search_id}").status_code == 204
    assert client.get(f"/api/searches/{search_id}").status_code == 404


def test_about(client):
    d = client.get("/").json()
    assert d["author"] == "Toan Tran" and "PM Accelerator" in d["about"]


def test_validation_errors(client):
    bad_dates = {"location": "Paris", "start_date": "2026-02-01", "end_date": "2026-01-01"}
    assert client.post("/api/searches", json=bad_dates).status_code == 400
    assert client.post("/api/searches", json={"location": "Nowhereville", "start_date": "2026-01-01", "end_date": "2026-01-02"}).status_code == 404
    assert client.get("/api/weather?location=").status_code == 400
    assert client.get("/api/weather?location=95,200").status_code == 400
    weather_response = client.get("/api/weather?location=Paris").json()
    assert weather_response["current"]["conditions"] == "Mainly clear"
    assert weather_response["about"] == "A city."
    assert weather_response["current"]["code"] == 1
    assert weather_response["air_quality"]["us_aqi"] == 42
    assert weather_response["air_quality"]["category"] == "Good"
    assert weather_response["videos"][0]["title"] == "Paris travel guide"
    assert weather_response["videos"][0]["url"].endswith("video123")
