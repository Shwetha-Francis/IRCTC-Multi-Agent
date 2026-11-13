import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.train_tools import search_trains, search_stations


# Find a station using its name or code
def find_station(query):

    result = search_stations(query)

    if not result.get("success"):
        return {"status": "error", "message": "Station search failed."}

    stations = result.get("data", [])

    if len(stations) == 0:
        return {"status": "not_found", "message": "No matching station found."}

    if len(stations) == 1:
        return {"status": "success", "station": stations[0]}

    return {"status": "multiple", "stations": stations}


# Search trains using station codes
def train_search_agent(source, destination, date=None):
    return search_trains(source, destination, date)