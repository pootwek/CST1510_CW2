"""
fetch_data.py - get earthquake data and save it as DATA/raw.csv.

Run it with: python fetch_data.py
"""

from pathlib import Path

import pandas as pd
import requests

# Ask the earthquake API for events with a magnitude of at least 2.5.
URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
PARAMS = {"format": "geojson", "minmagnitude": 2.5, "limit": 500}
RECORDS_KEY = "features"

# Keep the useful earthquake details and give the columns shorter names.
RENAME = {
    "properties_mag": "mag",
    "properties_place": "place",
    "properties_time": "time",
    "properties_magType": "mag_type",
    "properties_sig": "significance",
    "properties_tsunami": "tsunami",
}
KEEP = ["time", "place", "mag", "mag_type", "depth_km", "significance", "tsunami"]
MUST_HAVE = ["mag"]

RAW_FILE = Path(__file__).parent / "DATA" / "raw.csv"


def get_data(url, params):
    """Request the data and return it, or None if the request fails."""
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        print("Could not get the data:", error)
        return None


def make_table(data, records_key):
    """Turn the API records into a pandas table."""
    records = data[records_key] if records_key else data
    return pd.json_normalize(records, sep="_")


def tidy_data(df):
    """Keep the useful columns, make them clearer and remove empty magnitudes."""
    df = df.rename(columns=RENAME)
    df["depth_km"] = df["geometry_coordinates"].apply(lambda coords: coords[2])
    df["time"] = pd.to_datetime(df["time"], unit="ms").dt.strftime("%Y-%m-%d %H:%M:%S")
    df = df[KEEP]
    df = df.dropna(subset=MUST_HAVE)
    return df


def save_data(df, path):
    """Save the finished table as a CSV file."""
    path.parent.mkdir(exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {path}")


if __name__ == "__main__":
    data = get_data(URL, PARAMS)
    if data is not None:
        table = make_table(data, RECORDS_KEY)
        table = tidy_data(table)
        print(table.head())
        save_data(table, RAW_FILE)
