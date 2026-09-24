#!/usr/bin/env python3
"""
Backfill Statistics for Calculated Energy Sensors

This script calculates historical values for template sensors and imports them
into Home Assistant's statistics database using the recorder.import_statistics service.

Target sensors:
- sensor.inverter_power_consumption (Tesla solar - Emporia solar)
- sensor.battery_charging_loss (battery_charged * 0.05)
- sensor.battery_discharging_loss (battery_discharged * 0.0526)
- sensor.battery_total_efficiency_loss (charging_loss + discharging_loss)

Usage:
    python backfill_statistics.py --days 30 --dry-run
    python backfill_statistics.py --days 30 --execute
"""

import argparse
import json
from datetime import datetime, timedelta, timezone
from influxdb_client import InfluxDBClient
import requests

# Configuration - Update these values
HA_URL = "http://homeassistant.local:8123"  # Your Home Assistant URL
HA_TOKEN = "YOUR_LONG_LIVED_ACCESS_TOKEN"   # Create in HA Profile

INFLUX_URL = "http://192.168.1.63:8086"
INFLUX_TOKEN = "YOUR_INFLUXDB_TOKEN"  # From secrets.yaml
INFLUX_ORG = "home"
INFLUX_BUCKET = "iot"


def query_influxdb_hourly(entity_id: str, days: int) -> dict:
    """Query InfluxDB for hourly max values of an entity."""
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()
    
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r["entity_id"] == "{entity_id}")
      |> filter(fn: (r) => r["_field"] == "value")
      |> aggregateWindow(every: 1h, fn: max, createEmpty: false)
    '''
    
    result = query_api.query(query)
    
    data = {}
    for table in result:
        for record in table.records:
            timestamp = record.get_time()
            value = record.get_value()
            if value is not None:
                # Round to start of hour
                hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                data[hour_key] = value
    
    client.close()
    return data


def calculate_inverter_consumption(tesla_solar: dict, emporia_solar: dict) -> dict:
    """Calculate inverter power consumption (Tesla - Emporia solar)."""
    result = {}
    for ts, tesla_val in tesla_solar.items():
        emporia_val = emporia_solar.get(ts, 0)
        diff = tesla_val - emporia_val
        result[ts] = round(diff, 3) if diff > 0 else 0
    return result


def calculate_battery_charging_loss(battery_charged: dict) -> dict:
    """Calculate battery charging loss (5% of charged)."""
    return {ts: round(val * 0.05, 3) for ts, val in battery_charged.items()}


def calculate_battery_discharging_loss(battery_discharged: dict) -> dict:
    """Calculate battery discharging loss (5.26% of discharged)."""
    return {ts: round(val * 0.0526, 3) for ts, val in battery_discharged.items()}


def calculate_battery_total_loss(battery_charged: dict, battery_discharged: dict) -> dict:
    """Calculate total battery efficiency loss."""
    result = {}
    all_timestamps = set(battery_charged.keys()) | set(battery_discharged.keys())
    for ts in all_timestamps:
        charge_loss = battery_charged.get(ts, 0) * 0.05
        discharge_loss = battery_discharged.get(ts, 0) * 0.0526
        result[ts] = round(charge_loss + discharge_loss, 3)
    return result


def format_statistics_for_import(entity_id: str, data: dict, source_entity: str) -> list:
    """Format data for Home Assistant's recorder.import_statistics service."""
    statistics = []
    sorted_times = sorted(data.keys())
    
    for i, ts in enumerate(sorted_times):
        stat = {
            "start": ts.isoformat(),
            "state": data[ts],
            "sum": data[ts],  # For total sensors, state = sum at that point
        }
        statistics.append(stat)
    
    return statistics


def import_to_home_assistant(entity_id: str, statistics: list, dry_run: bool = True):
    """Import statistics to Home Assistant using the recorder service."""
    if dry_run:
        print(f"\n[DRY RUN] Would import {len(statistics)} records for {entity_id}")
        if statistics:
            print(f"  First: {statistics[0]['start']} = {statistics[0]['state']}")
            print(f"  Last:  {statistics[-1]['start']} = {statistics[-1]['state']}")
        return
    
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "statistic_id": entity_id,
        "source": "recorder",
        "unit_of_measurement": "kWh",
        "has_mean": False,
        "has_sum": True,
        "stats": statistics,
    }
    
    response = requests.post(
        f"{HA_URL}/api/services/recorder/import_statistics",
        headers=headers,
        json=payload,
    )
    
    if response.status_code == 200:
        print(f"✓ Imported {len(statistics)} records for {entity_id}")
    else:
        print(f"✗ Failed to import {entity_id}: {response.status_code} - {response.text}")


def main():
    parser = argparse.ArgumentParser(description="Backfill statistics for calculated energy sensors")
    parser.add_argument("--days", type=int, default=30, help="Number of days to backfill")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without importing")
    parser.add_argument("--execute", action="store_true", help="Actually import the statistics")
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print("Please specify --dry-run or --execute")
        return
    
    print(f"Querying InfluxDB for {args.days} days of historical data...")
    
    # Query source sensors from InfluxDB
    print("  - Fetching Tesla solar data...")
    tesla_solar = query_influxdb_hourly("west_sacramento_solar_generated", args.days)
    
    print("  - Fetching Emporia solar data...")
    emporia_solar = query_influxdb_hourly("solar_energy_today", args.days)
    
    print("  - Fetching battery charged data...")
    battery_charged = query_influxdb_hourly("west_sacramento_battery_charged", args.days)
    
    print("  - Fetching battery discharged data...")
    battery_discharged = query_influxdb_hourly("west_sacramento_battery_discharged", args.days)
    
    print(f"\nData points found:")
    print(f"  Tesla Solar: {len(tesla_solar)}")
    print(f"  Emporia Solar: {len(emporia_solar)}")
    print(f"  Battery Charged: {len(battery_charged)}")
    print(f"  Battery Discharged: {len(battery_discharged)}")
    
    # Calculate derived values
    print("\nCalculating derived sensor values...")
    
    inverter_consumption = calculate_inverter_consumption(tesla_solar, emporia_solar)
    charging_loss = calculate_battery_charging_loss(battery_charged)
    discharging_loss = calculate_battery_discharging_loss(battery_discharged)
    total_loss = calculate_battery_total_loss(battery_charged, battery_discharged)
    
    # Prepare for import
    sensors_to_import = [
        ("sensor.inverter_power_consumption", inverter_consumption, "west_sacramento_solar_generated"),
        ("sensor.battery_charging_loss", charging_loss, "west_sacramento_battery_charged"),
        ("sensor.battery_discharging_loss", discharging_loss, "west_sacramento_battery_discharged"),
        ("sensor.battery_total_efficiency_loss", total_loss, "west_sacramento_battery_charged"),
    ]
    
    dry_run = args.dry_run
    
    for entity_id, data, source in sensors_to_import:
        if data:
            statistics = format_statistics_for_import(entity_id, data, source)
            import_to_home_assistant(entity_id, statistics, dry_run=dry_run)
        else:
            print(f"⚠ No data to import for {entity_id}")
    
    if dry_run:
        print("\n" + "="*60)
        print("This was a DRY RUN. No data was imported.")
        print("Run with --execute to actually import the statistics.")
        print("="*60)


if __name__ == "__main__":
    main()

