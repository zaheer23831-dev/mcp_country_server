import requests

def register(mcp):
    @mcp.tool(
        id="country/info",
        name="Country Info",
        description="Get structured information about a country by name",
        input_schema={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "e.g. 'france'"}},
            "required": ["name"],
            "additionalProperties": False
        }
    )
    def country_info(input_):
        name = input_["name"]
        url = f"https://restcountries.com/v3.1/name/{name}"
        res = requests.get(url, timeout=20)
        res.raise_for_status()
        data = res.json()[0]
        return {
            "name": data["name"]["common"],
            "official_name": data["name"]["official"],
            "capital": (data.get("capital") or [None])[0],
            "region": data.get("region"),
            "subregion": data.get("subregion"),
            "population": data.get("population"),
            "area_km2": data.get("area"),
            "languages": list((data.get("languages") or {}).values()),
            "currency": (list((data.get("currencies") or {}).values())[0]["name"] if data.get("currencies") else None),
            "symbol": (list((data.get("currencies") or {}).values())[0].get("symbol") if data.get("currencies") else None),
            "flag": data.get("flag"),
            "maps": (data.get("maps") or {}).get("googleMaps"),
            "borders": data.get("borders") or [],
        }
