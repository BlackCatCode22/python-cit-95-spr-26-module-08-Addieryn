import requests
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

HEADERS = {"User-Agent": "FCC-Student-App"}

NWS_LOCATIONS = {
    "Fresno": (36.7378, -119.7871),
    "New York": (40.7128, -74.0060)
}

_forecast_url_cache = {}

def get_forecast_url(lat, lon):
    key = (lat, lon)
    if key in _forecast_url_cache:
        return _forecast_url_cache[key]
    url = f"https://api.weather.gov/points/{lat},{lon}"
    response = requests.get(url, headers=HEADERS, timeout=15)
    data = response.json()
    forecast_url = data["properties"]["forecast"]
    _forecast_url_cache[key] = forecast_url
    return forecast_url

def get_weather_nws(lat, lon):
    try:
        forecast_url = get_forecast_url(lat, lon)
        response = requests.get(forecast_url, headers=HEADERS, timeout=15)
        data = response.json()
        period = data["properties"]["periods"][0]
        return {
            "temp": period["temperature"],
            "unit": period["temperatureUnit"],
            "conditions": period["shortForecast"],
            "wind": period["windSpeed"],
            "wind_dir": period["windDirection"],
            "name": period["name"],
            "is_daytime": period["isDaytime"]
        }
    except Exception as e:
        return {"error": str(e)}

def get_weather_london():
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=51.5074&longitude=-0.1278"
            "&current=temperature_2m,weathercode,windspeed_10m,winddirection_10m,is_day"
            "&temperature_unit=fahrenheit"
            "&windspeed_unit=mph"
            "&timezone=Europe/London"
        )
        response = requests.get(url, timeout=15)
        data = response.json()
        current = data["current"]

        wmo_codes = {
            0: "Clear Sky", 1: "Mostly Clear", 2: "Partly Cloudy", 3: "Overcast",
            45: "Foggy", 48: "Icy Fog",
            51: "Light Drizzle", 53: "Drizzle", 55: "Heavy Drizzle",
            61: "Light Rain", 63: "Rain", 65: "Heavy Rain",
            71: "Light Snow", 73: "Snow", 75: "Heavy Snow",
            80: "Rain Showers", 81: "Rain Showers", 82: "Violent Rain Showers",
            95: "Thunderstorm", 96: "Thunderstorm w/ Hail", 99: "Thunderstorm w/ Hail"
        }
        code = current["weathercode"]
        conditions = wmo_codes.get(code, "Unknown")

        dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
        deg = current["winddirection_10m"]
        wind_dir = dirs[round(deg / 22.5) % 16]

        return {
            "temp": round(current["temperature_2m"]),
            "unit": "F",
            "conditions": conditions,
            "wind": f"{round(current['windspeed_10m'])} mph",
            "wind_dir": wind_dir,
            "name": "Current",
            "is_daytime": current["is_day"] == 1
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    fresno = get_weather_nws(*NWS_LOCATIONS["Fresno"])
    new_york = get_weather_nws(*NWS_LOCATIONS["New York"])
    london = get_weather_london()

    def weather_card(city, data, badge=None):
        if "error" in data:
            return f'<div class="card error"><h2>{city}</h2><p>Could not load weather: {data["error"]}</p></div>'

        icon = "☀️" if data["is_daytime"] else "🌙"
        if "Rain" in data["conditions"]: icon = "🌧️"
        elif "Snow" in data["conditions"]: icon = "❄️"
        elif "Cloud" in data["conditions"] or "Overcast" in data["conditions"]: icon = "☁️"
        elif "Thunder" in data["conditions"]: icon = "⛈️"
        elif "Fog" in data["conditions"]: icon = "🌫️"
        elif "Drizzle" in data["conditions"]: icon = "🌦️"

        badge_html = f'<span class="badge">{badge}</span>' if badge else ""

        return f"""
        <div class="card {'london' if badge else ''}">
            <div class="card-header">
                <span class="city">{city} {badge_html}</span>
                <span class="period">{data['name']}</span>
            </div>
            <div class="temp-row">
                <span class="icon">{icon}</span>
                <span class="temp">{data['temp']}°{data['unit']}</span>
            </div>
            <div class="conditions">{data['conditions']}</div>
            <div class="wind">💨 {data['wind']} {data['wind_dir']}</div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Weather Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">
        <style>
            *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

            :root {{
                --bg: #0a0a0f;
                --surface: #111118;
                --border: #1e1e2e;
                --accent: #c8f04a;
                --accent-dim: #8aaa28;
                --text: #e8e8f0;
                --muted: #6b6b80;
                --london: #7eb8f7;
            }}

            body {{
                background: var(--bg);
                color: var(--text);
                font-family: 'DM Mono', monospace;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 2rem;
            }}

            body::before {{
                content: '';
                position: fixed;
                inset: 0;
                background: radial-gradient(ellipse 80% 50% at 50% -10%, #c8f04a18, transparent);
                pointer-events: none;
            }}

            header {{
                text-align: center;
                margin-bottom: 3rem;
                animation: fadeDown 0.6s ease both;
            }}

            header h1 {{
                font-family: 'Syne', sans-serif;
                font-size: clamp(2rem, 5vw, 3.5rem);
                font-weight: 800;
                letter-spacing: -0.03em;
                line-height: 1;
            }}

            header h1 span {{ color: var(--accent); }}

            header p {{
                color: var(--muted);
                font-size: 0.8rem;
                letter-spacing: 0.15em;
                text-transform: uppercase;
                margin-top: 0.75rem;
            }}

            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 1.5rem;
                width: 100%;
                max-width: 1000px;
            }}

            .card {{
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 2rem;
                position: relative;
                overflow: hidden;
                animation: fadeUp 0.7s ease both;
                transition: transform 0.2s ease, border-color 0.2s ease;
            }}

            .card:hover {{
                transform: translateY(-4px);
                border-color: var(--accent-dim);
            }}

            .card::before {{
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, var(--accent), transparent);
                opacity: 0.5;
            }}

            .card.london::before {{
                background: linear-gradient(90deg, transparent, var(--london), transparent);
            }}

            .card.london:hover {{ border-color: var(--london); }}

            .card:nth-child(2) {{ animation-delay: 0.15s; }}
            .card:nth-child(3) {{ animation-delay: 0.3s; }}

            .card-header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 1.5rem;
            }}

            .city {{
                font-family: 'Syne', sans-serif;
                font-size: 1.4rem;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}

            .badge {{
                font-size: 0.6rem;
                font-family: 'DM Mono', monospace;
                background: #7eb8f720;
                color: var(--london);
                border: 1px solid #7eb8f740;
                padding: 0.2rem 0.5rem;
                border-radius: 999px;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                vertical-align: middle;
            }}

            .period {{
                font-size: 0.7rem;
                color: var(--muted);
                text-transform: uppercase;
                letter-spacing: 0.1em;
                background: var(--border);
                padding: 0.3rem 0.6rem;
                border-radius: 999px;
                white-space: nowrap;
            }}

            .temp-row {{
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 1rem;
            }}

            .icon {{ font-size: 2.5rem; line-height: 1; }}

            .temp {{
                font-family: 'Syne', sans-serif;
                font-size: 3.5rem;
                font-weight: 800;
                color: var(--accent);
                line-height: 1;
                letter-spacing: -0.04em;
            }}

            .london .temp {{ color: var(--london); }}

            .conditions {{
                font-size: 0.9rem;
                color: var(--text);
                margin-bottom: 0.75rem;
            }}

            .wind {{ font-size: 0.75rem; color: var(--muted); }}

            .card.error {{ border-color: #ff4444; }}
            .card.error p {{ color: #ff8888; font-size: 0.85rem; margin-top: 0.5rem; }}

            .sources {{
                margin-top: 1rem;
                font-size: 0.65rem;
                color: #3a3a50;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                text-align: center;
            }}

            footer {{
                margin-top: 3rem;
                font-size: 0.7rem;
                color: var(--muted);
                letter-spacing: 0.1em;
                text-transform: uppercase;
                animation: fadeUp 0.9s ease both;
                animation-delay: 0.45s;
                text-align: center;
            }}

            @keyframes fadeDown {{
                from {{ opacity: 0; transform: translateY(-16px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            @keyframes fadeUp {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>Live <span>Weather</span></h1>
            <p>Multi-Source &mdash; Real-Time Global Data</p>
        </header>
        <div class="grid">
            {weather_card("Fresno", fresno)}
            {weather_card("New York", new_york)}
            {weather_card("London", london, badge="Open-Meteo")}
        </div>
        <div class="sources">
            🇺🇸 Fresno &amp; New York via api.weather.gov &nbsp;|&nbsp; 🇬🇧 London via api.open-meteo.com
        </div>
        <footer>FCC-Student-App &bull; CIT-95</footer>
    </body>
    </html>
    """
    return HTMLResponse(content=html)