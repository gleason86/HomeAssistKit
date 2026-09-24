"""Quick test to set lights to blue."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ha_client import HomeAssistantClient


async def main():
    client = HomeAssistantClient()

    lights = ["light.bedroom", "light.bathroom", "light.living_room"]

    async with client:
        for light in lights:
            try:
                await client.call_service(
                    domain="light",
                    service="turn_on",
                    data={"rgb_color": [0, 0, 255]},
                    target={"entity_id": light},
                )
                print(f"[OK] {light} -> blue")
            except Exception as e:
                print(f"[FAIL] {light}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
