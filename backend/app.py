# FastAPI routes for weather lookups and saved-search management
import csv
import io
import json
import os
import uvicorn

from datetime import date, datetime, timezone
from fastapi import FastAPI, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from database import execute_sql, get_search_record, search_record_from_row
from services import (
    air_quality,
    check_dates,
    current_weather,
    daily_temps,
    geocode,
    map_info,
    optional,
    wiki_summary,
    youtube_search_url,
    youtube_videos,
)
from settings import ApiError, COMPANY_DESCRIPTION


class SearchCreateRequest(BaseModel):
    location: str
    start_date: date
    end_date: date
    note: str = Field("", max_length=500)


class SearchUpdateRequest(BaseModel):
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    note: str | None = Field(None, max_length=500)


app = FastAPI(title="Weather API", description="Backend assessment by Toan Tran. " + COMPANY_DESCRIPTION)


@app.exception_handler(ApiError)
async def on_api_error(_, error):
    return JSONResponse({"error": error.message}, status_code=error.status)


@app.exception_handler(RequestValidationError)
async def on_invalid_body(_, error):
    validation_error = error.errors()[0]
    return JSONResponse({"error": f"{validation_error['loc'][-1]}: {validation_error['msg']}"}, status_code=400)


@app.get("/")
def about():
    return {
        "app": "Weather API (backend assessment)",
        "author": "Toan Tran",
        "about": COMPANY_DESCRIPTION,
        "docs": "/docs",
    }


@app.get("/api/weather")
def get_weather(location: str = ""):
    location_data = geocode(location)
    return {
        "location": location_data,
        "current": current_weather(location_data),
        "about": optional(wiki_summary, location_data),
        "air_quality": optional(air_quality, location_data),
        "videos": optional(youtube_videos, location_data) or [],
        "youtube_search_url": youtube_search_url(location_data),
        **map_info(location_data),
    }


@app.post("/api/searches", status_code=201)
def create_search(search_request: SearchCreateRequest):
    check_dates(search_request.start_date, search_request.end_date)
    location_data = geocode(search_request.location)
    daily_temperatures = daily_temps(location_data, search_request.start_date, search_request.end_date)
    _, search_id = execute_sql(
        "INSERT INTO searches(query,name,lat,lon,start_date,end_date,temps,note,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
        (
            search_request.location.strip(),
            location_data["name"],
            location_data["lat"],
            location_data["lon"],
            search_request.start_date.isoformat(),
            search_request.end_date.isoformat(),
            json.dumps(daily_temperatures),
            search_request.note,
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
        ),
    )
    return {**get_search_record(search_id), **map_info(location_data)}


@app.get("/api/searches")
def list_all(query: str = Query(default="", alias="q")):
    search_pattern = f"%{query}%"
    search_rows, _ = execute_sql(
        "SELECT * FROM searches WHERE name LIKE ? OR note LIKE ? ORDER BY id DESC",
        (search_pattern, search_pattern),
    )
    return [search_record_from_row(row) for row in search_rows]


@app.get("/api/searches/{search_id}")
def get_search(search_id: int):
    search_record = get_search_record(search_id)
    return {**search_record, **map_info(search_record)}


@app.put("/api/searches/{search_id}")
def update_search(search_id: int, search_update: SearchUpdateRequest):
    search_record = get_search_record(search_id)
    start_date = search_update.start_date or date.fromisoformat(search_record["start_date"])
    end_date = search_update.end_date or date.fromisoformat(search_record["end_date"])
    check_dates(start_date, end_date)
    location_data = (
        geocode(search_update.location)
        if search_update.location
        else {
            "name": search_record["name"],
            "lat": search_record["lat"],
            "lon": search_record["lon"],
        }
    )
    daily_temperatures = daily_temps(location_data, start_date, end_date)
    note = search_record["note"] if search_update.note is None else search_update.note
    execute_sql(
        "UPDATE searches SET name=?,lat=?,lon=?,start_date=?,end_date=?,temps=?,note=? WHERE id=?",
        (
            location_data["name"],
            location_data["lat"],
            location_data["lon"],
            start_date.isoformat(),
            end_date.isoformat(),
            json.dumps(daily_temperatures),
            note,
            search_id,
        ),
    )
    return get_search_record(search_id)


@app.delete("/api/searches/{search_id}", status_code=204)
def delete_search(search_id: int):
    get_search_record(search_id)
    execute_sql("DELETE FROM searches WHERE id=?", (search_id,))
    return Response(status_code=204)


@app.get("/api/export")
def export(export_format: str = Query(default="json", alias="format")):
    export_format = export_format.lower()
    search_records = [
        search_record_from_row(row)
        for row in execute_sql("SELECT * FROM searches ORDER BY id")[0]
    ]
    attachment_headers = {"Content-Disposition": f"attachment; filename=weather_export.{export_format}"}
    if export_format == "json":
        return Response(
            json.dumps(search_records, indent=2),
            media_type="application/json",
            headers=attachment_headers,
        )
    if export_format == "csv":
        csv_rows = [
            {
                "id": record["id"],
                "location": record["name"],
                "date": day["date"],
                "max_c": day["max_c"],
                "min_c": day["min_c"],
                "precip_mm": day.get("precip_mm"),
                "note": record["note"],
            }
            for record in search_records
            for day in record["temps"]
        ]
        columns = ["id", "location", "date", "max_c", "min_c", "precip_mm", "note"]
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=columns)
        writer.writeheader()
        writer.writerows(csv_rows)
        return Response(csv_buffer.getvalue(), media_type="text/csv", headers=attachment_headers)
    raise ApiError("format must be one of: json, csv")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5000, reload=os.environ.get("DEBUG") == "1")
