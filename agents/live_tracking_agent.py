import sys
from pathlib import Path
import requests

# Add the project folder so Python can import train_tools.
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from tools.train_tools import get_live_tracking


def live_tracking_agent(train_number, date=None):

    # Get live tracking information from RailRadar.
    result = get_live_tracking(train_number, date)

    if not result.get("success"):
        print("Unable to get train information.")
        return

    data = result.get("data", {})

    print("\n========== LIVE TRAIN STATUS ==========")
    print("Train Number:", data.get("trainNumber"))
    print("Train Name:", data.get("trainName"))
    print("Running Status:", data.get("status"))
    print("Last Updated:", data.get("lastUpdatedAt"))

    # Current location details.
    current = data.get("currentLocation") or {}

    print("\n========== CURRENT LOCATION ==========")
    print("Station:", current.get("stationName", "Not available"))
    print("Station Code:", current.get("stationCode", "Not available"))
    print("Distance from Origin:", current.get("distanceFromOriginKm", "Not available"), "km")
    print("Speed:", current.get("speedKmh", "Not available"), "km/h")
    print("Delay:", current.get("delayMinutes", "Not available"), "minutes")

    # Next halt details.
    next_halt = data.get("nextHalt") or {}

    print("\n========== NEXT HALT ==========")
    print("Station:", next_halt.get("stationName", "Not available"))
    print("Station Code:", next_halt.get("stationCode", "Not available"))

    # Display only the next five route stations.
    route = data.get("route", [])
    current_sequence = current.get("sequence", 0)

    upcoming = [
    station for station in route
    if station.get("sequence", 0) > current_sequence
    and station.get("isHalt") is True
    ]

    print("\n========== UPCOMING STATIONS ==========")

    for station in upcoming[:5]:
        print(
            station.get("stationName"),
            "| Arrival:", station.get("scheduledArrival", "N/A"),
            "| Departure:", station.get("scheduledDeparture", "N/A")
        )


if __name__ == "__main__":

    print("\nIRCTC Live Train Tracking Agent")
    print("Type 'exit' to stop.\n")

    while True:
        train_number = input("Enter train number: ").strip()

        if train_number.lower() == "exit":
            print("Goodbye!")
            break

        if not train_number:
            print("Please enter a train number.\n")
            continue

        date = input("Journey date (YYYY-MM-DD) or Enter: ").strip()
        date = date if date else None

        try:
            live_tracking_agent(train_number, date)

        except requests.RequestException as error:
            print("API request failed:", error)

        except Exception as error:
            print("Error:", error)

        print()
