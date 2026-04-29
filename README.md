# FRA Rail Crossing Flood Risk Monitor

An interactive web app that maps at-grade railroad crossings within a user-defined radius and overlays real-time flood risk using NOAA National Weather Service alerts and OpenWeatherMap precipitation data.

## Features

- Query the live **FRA Highway-Rail Grade Crossing** database by center point and radius (1–100 miles)
- Real-time **flood risk classification** per crossing:
  - 🔴 **Critical** — Active NWS Flood Warning / Flash Flood Warning
  - 🟠 **High** — Active NWS Flood Watch / Flash Flood Watch
  - 🟡 **Moderate** — Heavy rain (≥ 0.1 in/hr), no active alert
  - 🟢 **Low** — No alerts, minimal precipitation
- Click the map or enter coordinates to set the center point
- Sidebar lists all crossings sorted by risk, active alert headlines, and summary stats
- Click any crossing marker or list item for full details (ID, railroad, AADT, street, city)

## Data Sources

| Source | API | Auth |
|---|---|---|
| FRA Grade Crossings | [FRAGIS ArcGIS REST](https://fragis.fra.dot.gov/arcgis/rest/services/FRA/FRAAtGradeX_iOS/MapServer) | None |
| Flood Alerts | [NOAA NWS Alerts API](https://www.weather.gov/documentation/services-web-api) | None |
| Precipitation | [OpenWeatherMap Current Weather](https://openweathermap.org/api) | Free API key |

## Setup

```bash
git clone https://github.com/Zach-Guilfoyle/fra-flood-crossing-monitor.git
cd fra-flood-crossing-monitor

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your OpenWeatherMap API key
```

Get a free OpenWeatherMap API key at https://openweathermap.org/api

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

## Tech Stack

- **Backend**: Python / Flask
- **Frontend**: Leaflet.js, vanilla JS, HTML/CSS
- **APIs**: FRA FRAGIS ArcGIS REST, NOAA NWS, OpenWeatherMap
