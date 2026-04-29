import math
import json
import os
import urllib3
import requests
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

load_dotenv()

# FRAGIS has a self-signed cert; suppress the warning for that host only
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

OWM_API_KEY = os.environ.get("OWM_API_KEY", "")

FRA_URL = "https://fragis.fra.dot.gov/arcgis/rest/services/FRA/FRAAtGradeX_iOS/MapServer/0/query"
NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"
OWM_URL = "https://api.openweathermap.org/data/2.5/weather"

# NWS event severity ordering
FLOOD_WARNING_EVENTS = {
    "Flood Warning",
    "Flash Flood Warning",
    "Areal Flood Warning",
}
FLOOD_WATCH_EVENTS = {
    "Flood Watch",
    "Flash Flood Watch",
    "Areal Flood Watch",
    "Areal Flood Advisory",
    "Flood Advisory",
}


def miles_to_meters(miles: float) -> float:
    return miles * 1609.344


def offset_point(lat: float, lon: float, bearing_deg: float, miles: float):
    """Return a lat/lon offset from a center point by `miles` in the given bearing."""
    R = 3958.8  # Earth radius in miles
    bearing = math.radians(bearing_deg)
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    d = miles / R
    new_lat = math.asin(
        math.sin(lat_r) * math.cos(d) + math.cos(lat_r) * math.sin(d) * math.cos(bearing)
    )
    new_lon = lon_r + math.atan2(
        math.sin(bearing) * math.sin(d) * math.cos(lat_r),
        math.cos(d) - math.sin(lat_r) * math.sin(new_lat),
    )
    return math.degrees(new_lat), math.degrees(new_lon)


def fetch_nws_alerts(lat: float, lon: float) -> list:
    """Fetch active NWS alerts for a given point. Returns list of alert feature dicts."""
    try:
        resp = requests.get(
            NWS_ALERTS_URL,
            params={"point": f"{lat:.4f},{lon:.4f}"},
            headers={"User-Agent": "FRA-Flood-Monitor/1.0 contact@example.com"},
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json().get("features", [])
    except Exception:
        return []


def classify_nws_alerts(alerts: list) -> tuple[str, list]:
    """
    Given a list of NWS alert features, return (risk_level, alert_summaries).
    risk_level: "warning" | "watch" | "none"
    """
    risk = "none"
    summaries = []
    for feature in alerts:
        props = feature.get("properties", {})
        event = props.get("event", "")
        headline = props.get("headline") or props.get("description", "")[:120]
        if event in FLOOD_WARNING_EVENTS:
            risk = "warning"
            summaries.append({"event": event, "headline": headline})
        elif event in FLOOD_WATCH_EVENTS and risk != "warning":
            risk = "watch"
            summaries.append({"event": event, "headline": headline})
    return risk, summaries


def fetch_precipitation(lat: float, lon: float) -> float:
    """Return current 1-hour precipitation in inches (0.0 if none)."""
    try:
        resp = requests.get(
            OWM_URL,
            params={
                "lat": lat,
                "lon": lon,
                "appid": OWM_API_KEY,
                "units": "imperial",
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        rain = data.get("rain", {})
        # OWM returns mm, convert to inches (1 mm = 0.03937 in)
        rain_mm = rain.get("1h", 0.0)
        return rain_mm * 0.03937
    except Exception:
        return 0.0


def assess_risk(nws_level: str, precip_in: float) -> str:
    if nws_level == "warning":
        return "critical"
    if nws_level == "watch":
        return "high"
    if precip_in >= 0.1:
        return "moderate"
    return "low"


def fetch_crossings(lat: float, lon: float, radius_miles: float) -> list:
    """Query FRA ArcGIS REST API for at-grade crossings within radius."""
    geometry = json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}})
    params = {
        "geometry": geometry,
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": miles_to_meters(radius_miles),
        "units": "esriSRUnit_Meter",
        "outFields": "CROSSING,StateCode,RAILROAD,LATITUDE,LONGITUD,POSXING,AADT,TYPEXING,STATENAME,COUNTYNAME,CITYNAME,HIGHWAY,STREET",
        "returnGeometry": "false",
        "resultRecordCount": 500,
        "f": "json",
    }
    try:
        resp = requests.get(FRA_URL, params=params, timeout=15, verify=False)
        resp.raise_for_status()
        data = resp.json()
        return data.get("features", [])
    except Exception as e:
        return []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/crossings")
def api_crossings():
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
        radius_miles = float(request.args.get("radius_miles", 25))
    except (KeyError, ValueError):
        return jsonify({"error": "lat, lon, and radius_miles are required"}), 400

    features = fetch_crossings(lat, lon, radius_miles)
    crossings = []
    for f in features:
        attrs = f.get("attributes", {})
        c_lat = attrs.get("LATITUDE")
        c_lon = attrs.get("LONGITUD")
        if c_lat is None or c_lon is None:
            continue
        crossings.append({
            "id": attrs.get("CROSSING", "N/A"),
            "railroad": attrs.get("RAILROAD", "Unknown"),
            "state": attrs.get("STATENAME") or attrs.get("StateCode", ""),
            "county": attrs.get("COUNTYNAME", ""),
            "city": attrs.get("CITYNAME", ""),
            "highway": attrs.get("HIGHWAY", ""),
            "street": attrs.get("STREET", ""),
            "aadt": attrs.get("AADT"),
            "type": attrs.get("TYPEXING"),
            "pos": attrs.get("POSXING"),
            "lat": c_lat,
            "lon": c_lon,
        })
    return jsonify({"count": len(crossings), "crossings": crossings})


@app.route("/api/weather-risk")
def api_weather_risk():
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon are required"}), 400

    alerts = fetch_nws_alerts(lat, lon)
    nws_level, summaries = classify_nws_alerts(alerts)
    precip = fetch_precipitation(lat, lon)
    risk = assess_risk(nws_level, precip)

    return jsonify({
        "risk": risk,
        "nws_level": nws_level,
        "precip_in_per_hr": round(precip, 4),
        "alerts": summaries,
    })


@app.route("/api/assess")
def api_assess():
    """Main endpoint: crossings + flood risk assessment for the search area."""
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
        radius_miles = float(request.args.get("radius_miles", 25))
    except (KeyError, ValueError):
        return jsonify({"error": "lat, lon, and radius_miles are required"}), 400

    # Fetch crossings
    features = fetch_crossings(lat, lon, radius_miles)

    # Fetch weather/flood data: center + 4 cardinal edge points
    sample_points = [(lat, lon)]
    for bearing in (0, 90, 180, 270):
        sample_points.append(offset_point(lat, lon, bearing, radius_miles * 0.85))

    all_alerts = []
    worst_nws = "none"
    for slat, slon in sample_points:
        a = fetch_nws_alerts(slat, slon)
        level, summaries = classify_nws_alerts(a)
        all_alerts.extend(summaries)
        if level == "warning":
            worst_nws = "warning"
        elif level == "watch" and worst_nws != "warning":
            worst_nws = "watch"

    # Deduplicate alerts by event+headline
    seen = set()
    unique_alerts = []
    for al in all_alerts:
        key = al["event"] + al["headline"][:40]
        if key not in seen:
            seen.add(key)
            unique_alerts.append(al)

    precip = fetch_precipitation(lat, lon)
    area_risk = assess_risk(worst_nws, precip)

    crossings = []
    for f in features:
        attrs = f.get("attributes", {})
        c_lat = attrs.get("LATITUDE")
        c_lon = attrs.get("LONGITUD")
        if c_lat is None or c_lon is None:
            continue
        crossings.append({
            "id": attrs.get("CROSSING", "N/A"),
            "railroad": attrs.get("RAILROAD", "Unknown"),
            "state": attrs.get("STATENAME") or attrs.get("StateCode", ""),
            "county": attrs.get("COUNTYNAME", ""),
            "city": attrs.get("CITYNAME", ""),
            "highway": attrs.get("HIGHWAY", ""),
            "street": attrs.get("STREET", ""),
            "aadt": attrs.get("AADT"),
            "type": attrs.get("TYPEXING"),
            "pos": attrs.get("POSXING"),
            "lat": c_lat,
            "lon": c_lon,
            "risk": area_risk,
        })

    risk_counts = {"critical": 0, "high": 0, "moderate": 0, "low": 0}
    for c in crossings:
        risk_counts[c["risk"]] = risk_counts.get(c["risk"], 0) + 1

    return jsonify({
        "center": {"lat": lat, "lon": lon},
        "radius_miles": radius_miles,
        "area_risk": area_risk,
        "nws_level": worst_nws,
        "precip_in_per_hr": round(precip, 4),
        "alerts": unique_alerts,
        "risk_counts": risk_counts,
        "total": len(crossings),
        "crossings": crossings,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
