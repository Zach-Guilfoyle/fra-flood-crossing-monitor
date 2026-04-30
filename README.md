# FRA Rail Crossing Flood Risk Monitor

An interactive web app that maps at-grade railroad crossings within a user-defined radius and overlays real-time flood risk using NOAA National Weather Service alerts, OpenWeatherMap precipitation data, USGS stream gauges, and FEMA flood zone maps.

## Features

- Query the live **FRA Highway-Rail Grade Crossing** database by center point and radius (1–100 miles)
- Real-time **flood risk classification** per crossing:
  - 🔴 **Critical** — Active NWS Flood Warning / Flash Flood Warning
  - 🟠 **High** — Active NWS Flood Watch / Flash Flood Watch
  - 🟡 **Moderate** — Heavy rain (≥ 0.1 in/hr), no active alert
  - 🟢 **Low** — No alerts, minimal precipitation
- **FEMA Flood Zone overlay** (NFHL) with adjustable opacity — highlights 100-yr and 500-yr flood zones
- **USGS river gauge markers** showing live stream stage readings for gauges within the search area
- **Layer toggles** — individually show/hide risk tiers, search radius circle, flood zones, and gauges
- Click the map or enter coordinates to set the center point
- Sidebar lists all crossings sorted by risk, active alert headlines, and summary stats
- Click any crossing marker or list item for full details (ID, railroad, AADT, type, street, city, lat/lon)

## Data Sources

| Source | API | Auth |
|---|---|---|
| FRA Grade Crossings | [FRAGIS ArcGIS REST](https://fragis.fra.dot.gov/arcgis/rest/services/FRA/FRAAtGradeX_iOS/MapServer) | None |
| Flood Alerts | [NOAA NWS Alerts API](https://www.weather.gov/documentation/services-web-api) | None |
| Precipitation | [OpenWeatherMap Current Weather](https://openweathermap.org/api) | Free API key |
| Stream Gauges | [USGS NWIS Instantaneous Values](https://waterservices.usgs.gov/nwis/iv/) | None |
| Flood Zone Map | [FEMA NFHL ArcGIS REST](https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer) | None |

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
- **Frontend**: Leaflet.js, Esri Leaflet, vanilla JS, HTML/CSS
- **APIs**: FRA FRAGIS ArcGIS REST, NOAA NWS, OpenWeatherMap, USGS NWIS, FEMA NFHL
