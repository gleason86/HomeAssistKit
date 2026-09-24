"""Compare power usage: last hour today vs same hour yesterday."""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ha_client import HomeAssistantClient


async def main():
    client = HomeAssistantClient()

    async with client:
        # Get 26 hours of history to ensure we cover yesterday's same hour
        start_time = datetime.now() - timedelta(hours=26)
        history = await client.get_history(
            entity_id="sensor.west_sacramento_load_power",
            start_time=start_time,
            minimal_response=False
        )

        if not history or not history[0]:
            print("No history data available")
            return

        readings = history[0]

        # Get current local hour
        now_local = datetime.now()
        current_hour = now_local.hour
        today_date = now_local.date()
        yesterday_date = (now_local - timedelta(days=1)).date()

        # Separate today's and yesterday's readings for the same hour
        today_readings = []
        yesterday_readings = []

        # PST is UTC-8
        local_offset = -8

        for entry in readings:
            timestamp_str = entry.get("last_changed", "")
            state = entry.get("state", "")

            try:
                power = float(state)

                # Parse ISO timestamp with timezone
                if "+" in timestamp_str:
                    # Has timezone info - parse it
                    ts_utc = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    # Convert to local time (PST = UTC-8)
                    ts_local = ts_utc - timedelta(hours=8)
                else:
                    ts_local = datetime.fromisoformat(timestamp_str)

                # Check if this reading is from the target hour
                if ts_local.hour == current_hour:
                    reading_date = ts_local.date()

                    if reading_date == today_date:
                        today_readings.append((ts_local, power))
                    elif reading_date == yesterday_date:
                        yesterday_readings.append((ts_local, power))

            except (ValueError, TypeError) as e:
                continue

        # Calculate averages
        print("=" * 60)
        print(f"POWER COMPARISON: {current_hour}:00 - {current_hour}:59")
        print("=" * 60)

        print(f"\nTODAY ({today_date}) - Hour {current_hour}:00")
        if today_readings:
            powers_today = [p for _, p in today_readings]
            avg_today = sum(powers_today) / len(powers_today)
            min_today = min(powers_today)
            max_today = max(powers_today)
            first_time = min(t for t, _ in today_readings).strftime("%H:%M")
            last_time = max(t for t, _ in today_readings).strftime("%H:%M")
            print(f"  Readings: {len(today_readings)} ({first_time} - {last_time})")
            print(f"  Average:  {avg_today:.2f} kW ({avg_today*1000:.0f} W)")
            print(f"  Min:      {min_today:.2f} kW")
            print(f"  Max:      {max_today:.2f} kW")
        else:
            print("  No readings yet for this hour")
            avg_today = 0

        print(f"\nYESTERDAY ({yesterday_date}) - Hour {current_hour}:00")
        if yesterday_readings:
            powers_yesterday = [p for _, p in yesterday_readings]
            avg_yesterday = sum(powers_yesterday) / len(powers_yesterday)
            min_yesterday = min(powers_yesterday)
            max_yesterday = max(powers_yesterday)
            first_time = min(t for t, _ in yesterday_readings).strftime("%H:%M")
            last_time = max(t for t, _ in yesterday_readings).strftime("%H:%M")
            print(f"  Readings: {len(yesterday_readings)} ({first_time} - {last_time})")
            print(f"  Average:  {avg_yesterday:.2f} kW ({avg_yesterday*1000:.0f} W)")
            print(f"  Min:      {min_yesterday:.2f} kW")
            print(f"  Max:      {max_yesterday:.2f} kW")
        else:
            print("  No readings available for this hour yesterday")
            avg_yesterday = 0

        if today_readings and yesterday_readings:
            diff = avg_today - avg_yesterday
            pct = (diff / avg_yesterday) * 100 if avg_yesterday else 0
            print(f"\n{'='*60}")
            print("COMPARISON")
            print(f"{'='*60}")
            print(f"  Today's avg:     {avg_today:.2f} kW")
            print(f"  Yesterday's avg: {avg_yesterday:.2f} kW")
            print(f"  Difference:      {diff:+.2f} kW ({pct:+.1f}%)")
            print()
            if diff > 0.1:
                print(f"  >> Using MORE power than yesterday at this time")
            elif diff < -0.1:
                print(f"  >> Using LESS power than yesterday at this time")
            else:
                print(f"  >> About the same as yesterday")


if __name__ == "__main__":
    asyncio.run(main())
