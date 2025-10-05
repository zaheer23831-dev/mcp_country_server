"""
Example tool module: weather.info using @mcp.tool()
"""

import requests

def register(mcp):
    @mcp.tool(
        id="weather/info",
        name="Weather Info",
        description="Get the capital city's location info for a given country (for weather use).",
        input_schema={
            "type": "object",
            "properties": {
                "country": {"type": "string", "description": "Country name, e.g. 'france'"}
            },
            "required": ["country"],
            "additionalProperties": False
        }
    )
    def weather_info(input_):
        country = input_["country"]

        # Step 1: get capital from restcountries
        url_country = f"https://restcountries.com/v3.1/name/{country}"
        res_country = requests.get(url_country, timeout=20)
        res_country.raise_for_status()
        country_data = res_country.json()[0]
        capital = (country_data.get("capital") or [None])[0]
        if not capital:
            return {"error": f"Could not determine capital for {country}"}

        # Step 2: get coordinates of capital city from open-meteo geocoding API
        url_geo = f"https://geocoding-api.open-meteo.com/v1/search?name={capital}&count=1"
        res_geo = requests.get(url_geo, timeout=20)
        res_geo.raise_for_status()
        geo_data = res_geo.json()

        if not geo_data.get("results"):
            return {"error": f"No location found for {capital}"}

        location = geo_data["results"][0]

        return {
            "country": country_data["name"]["common"],
            "capital": capital,
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "timezone": location.get("timezone"),
            "population": country_data.get("population"),
            "note": "You can now query Open-Meteo weather API with these coordinates."
        }
