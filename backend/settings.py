# Shared settings and API error type used across the backend

from dotenv import load_dotenv

load_dotenv()

DB_PATH = "weather.db"
REQUEST_HEADERS = {"User-Agent": "weather-app-assessment/1.0"}
COMPANY_DESCRIPTION = (
    "PM Accelerator is a US-based company with a global reach, premiering in AI learning and as a development hub, "
    "featuring award-winning AI products and mentors from top-tier companies such as Google, Meta, Apple, and Nvidia. "
    "It offers a dynamic AI PM Bootcamp, designed to empower the next generation of AI professionals through "
    "hands-on experience, mentorship, and real-world projects. Website: https://www.pmaccelerator.io/"
)

WEATHER_CONDITIONS = {
    0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 61: "Light rain", 63: "Rain",
    65: "Heavy rain", 71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Showers",
    81: "Showers", 82: "Heavy showers", 95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm",
}


class ApiError(Exception):
    def __init__(self, message, status=400):
        self.message = message
        self.status = status
