"""Comprehensive test for all MCP Home Assistant tools."""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ha_client import HomeAssistantClient


class TestResults:
    """Track test results."""

    def __init__(self):
        self.passed = []
        self.failed = []

    def add_pass(self, name: str, details: str = ""):
        self.passed.append((name, details))
        print(f"  [PASS] {name}: {details}")

    def add_fail(self, name: str, error: str):
        self.failed.append((name, error))
        print(f"  [FAIL] {name}: {error}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        print("\n" + "=" * 60)
        print(f"TEST SUMMARY: {len(self.passed)}/{total} passed")
        print("=" * 60)
        if self.failed:
            print("\nFailed tests:")
            for name, error in self.failed:
                print(f"  [FAIL] {name}: {error}")
        return len(self.failed) == 0


async def test_all_tools():
    """Test all MCP tools."""
    results = TestResults()

    print("=" * 60)
    print("MCP HOME ASSISTANT TOOLS - COMPREHENSIVE TEST")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    try:
        client = HomeAssistantClient()
        print(f"\nConnecting to: {client.host}")
    except Exception as e:
        print(f"\n[FATAL] Could not initialize client: {e}")
        return False

    async with client:
        # =====================================================================
        # Test 1: ha_get_config
        # =====================================================================
        print("\n[1/12] Testing ha_get_config...")
        try:
            config = await client.get_config()
            version = config.get("version", "unknown")
            location = config.get("location_name", "unknown")
            results.add_pass("ha_get_config", f"HA v{version} @ {location}")
        except Exception as e:
            results.add_fail("ha_get_config", str(e))

        # =====================================================================
        # Test 2: ha_entity_summary
        # =====================================================================
        print("\n[2/12] Testing ha_entity_summary...")
        try:
            summary = await client.get_entity_summary()
            total = sum(summary.values())
            domains = len(summary)
            results.add_pass(
                "ha_entity_summary", f"{total} entities across {domains} domains"
            )
        except Exception as e:
            results.add_fail("ha_entity_summary", str(e))

        # =====================================================================
        # Test 3: ha_list_entities (with domain filter)
        # =====================================================================
        print("\n[3/12] Testing ha_list_entities...")
        try:
            # Test without filter first
            all_states = await client.get_states()
            results.add_pass(
                "ha_list_entities (all)", f"Found {len(all_states)} entities"
            )

            # Test with domain filter
            lights = await client.get_entities_by_domain("light")
            results.add_pass(
                "ha_list_entities (light)", f"Found {len(lights)} light entities"
            )
        except Exception as e:
            results.add_fail("ha_list_entities", str(e))

        # =====================================================================
        # Test 4: ha_get_state
        # =====================================================================
        print("\n[4/12] Testing ha_get_state...")
        try:
            # Find a real entity to test with
            states = await client.get_states()
            if states:
                test_entity = states[0]["entity_id"]
                state = await client.get_state(test_entity)
                entity_state = state.get("state", "unknown")
                results.add_pass("ha_get_state", f"{test_entity} = {entity_state}")
            else:
                results.add_fail("ha_get_state", "No entities found to test")
        except Exception as e:
            results.add_fail("ha_get_state", str(e))

        # =====================================================================
        # Test 5: ha_search_entities
        # =====================================================================
        print("\n[5/12] Testing ha_search_entities...")
        try:
            # Search for something common
            results_list = await client.search_entities("light")
            results.add_pass(
                "ha_search_entities", f"Found {len(results_list)} matches for 'light'"
            )
        except Exception as e:
            results.add_fail("ha_search_entities", str(e))

        # =====================================================================
        # Test 6: ha_get_history
        # =====================================================================
        print("\n[6/12] Testing ha_get_history...")
        try:
            # Get history for a sensor (they usually have good history)
            sensors = await client.get_entities_by_domain("sensor")
            if sensors:
                test_sensor = sensors[0]["entity_id"]
                start_time = datetime.now() - timedelta(hours=1)
                history = await client.get_history(
                    entity_id=test_sensor, start_time=start_time
                )
                if history and history[0]:
                    results.add_pass(
                        "ha_get_history",
                        f"{len(history[0])} state changes for {test_sensor}",
                    )
                else:
                    results.add_pass(
                        "ha_get_history", f"No recent changes for {test_sensor} (OK)"
                    )
            else:
                results.add_fail("ha_get_history", "No sensors to test with")
        except Exception as e:
            results.add_fail("ha_get_history", str(e))

        # =====================================================================
        # Test 7: ha_get_services
        # =====================================================================
        print("\n[7/12] Testing ha_get_services...")
        try:
            services = await client.get_services()
            # Count unique services
            service_count = sum(len(s.get("services", {})) for s in services)
            results.add_pass(
                "ha_get_services",
                f"Found {service_count} services across {len(services)} domains",
            )
        except Exception as e:
            results.add_fail("ha_get_services", str(e))

        # =====================================================================
        # Test 8: ha_get_logbook
        # =====================================================================
        print("\n[8/12] Testing ha_get_logbook...")
        try:
            start_time = datetime.now() - timedelta(hours=1)
            entries = await client.get_logbook(start_time=start_time)
            results.add_pass(
                "ha_get_logbook", f"Found {len(entries)} entries in last hour"
            )
        except Exception as e:
            results.add_fail("ha_get_logbook", str(e))

        # =====================================================================
        # Test 9: ha_render_template
        # =====================================================================
        print("\n[9/12] Testing ha_render_template...")
        try:
            # Simple template that should work on any HA instance
            template = "{{ now().strftime('%Y-%m-%d %H:%M') }}"
            result = await client.render_template(template)
            results.add_pass("ha_render_template", f"now() = {result.strip()}")

            # Test a more complex template
            template2 = "{{ states | count }} entities"
            result2 = await client.render_template(template2)
            results.add_pass(
                "ha_render_template (complex)", f"Result: {result2.strip()}"
            )
        except Exception as e:
            results.add_fail("ha_render_template", str(e))

        # =====================================================================
        # Test 10: ha_get_calendars
        # =====================================================================
        print("\n[10/12] Testing ha_get_calendars...")
        try:
            calendars = await client.get_calendars()
            if calendars:
                results.add_pass(
                    "ha_get_calendars", f"Found {len(calendars)} calendars"
                )

                # Try to get events from first calendar
                cal_id = calendars[0].get("entity_id")
                if cal_id:
                    events = await client.get_calendar_events(cal_id)
                    results.add_pass(
                        "ha_get_calendars (events)",
                        f"{len(events)} upcoming events in {cal_id}",
                    )
            else:
                results.add_pass("ha_get_calendars", "No calendars configured (OK)")
        except Exception as e:
            results.add_fail("ha_get_calendars", str(e))

        # =====================================================================
        # Test 11: ha_fire_event (safe test event)
        # =====================================================================
        print("\n[11/12] Testing ha_fire_event...")
        try:
            # Fire a harmless test event
            event_result = await client.fire_event(
                "mcp_test_event",
                {"test": True, "timestamp": datetime.now().isoformat()},
            )
            results.add_pass("ha_fire_event", "Fired 'mcp_test_event' successfully")
        except Exception as e:
            results.add_fail("ha_fire_event", str(e))

        # =====================================================================
        # Test 12: ha_call_service (safe test - input_button.press or logger)
        # =====================================================================
        print("\n[12/12] Testing ha_call_service...")
        try:
            # Try multiple safe approaches
            success = False

            # Approach 1: Check if there's an input_button to press (very safe)
            input_buttons = await client.get_entities_by_domain("input_button")
            if input_buttons and not success:
                test_entity = input_buttons[0]["entity_id"]
                await client.call_service(
                    domain="input_button",
                    service="press",
                    data={"entity_id": test_entity},
                )
                results.add_pass(
                    "ha_call_service", f"input_button.press on {test_entity}"
                )
                success = True

            # Approach 2: Try logger.set_level (harmless)
            if not success:
                await client.call_service(
                    domain="logger",
                    service="set_level",
                    data={"homeassistant.core": "info"},
                )
                results.add_pass(
                    "ha_call_service", "logger.set_level (safe service call)"
                )
                success = True
        except Exception as e:
            results.add_fail("ha_call_service", str(e))

    # Print summary
    return results.summary()


def main():
    """Run all tests."""
    success = asyncio.run(test_all_tools())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
