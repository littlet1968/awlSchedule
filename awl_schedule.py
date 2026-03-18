#!/usr/bin/env python3
"""Client for retrieving AWL garbage pickup information.

This module encapsulates the workflow described in ``awlSchedule.md``.
It handles configuration management, discovery of available streets
via the AWL API, and persistence of the selected street configuration.
"""

from __future__ import annotations

<<<<<<< HEAD
import curses
=======
import argparse
import curses
from datetime import datetime
>>>>>>> main
import json
import pathlib
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence

import requests


@dataclass
class AWLConfig:
    """Represents the persisted AWL configuration."""

    api_url: str = "https://buergerportal.awl-neuss.de/api/v1/calendar"
    streets_endpoint: str = "/townarea-streets"
    waste_bins: List[str] = field(
        default_factory=lambda: ["blau", "braun", "gelb", "grau", "pink"]
    )
    strasse_nummer: Optional[str] = None
    strasse_bezeichnung: Optional[str] = None

    @property
    def is_complete(self) -> bool:
<<<<<<< HEAD
        """Checks if configuration is complete."""
=======
        """Check that the configuration is OK."""
>>>>>>> main
        return bool(self.strasse_nummer and self.strasse_bezeichnung)


class AWLScheduleClient:
<<<<<<< HEAD
    """High-level client orchestrating configuration and street selection."""

    def __init__(self, config_path: str | pathlib.Path = "awl.conf") -> None:
        """Class configuration."""
=======
    """High-level AWL client."""

    def __init__(self, config_path: str | pathlib.Path = "awl.conf") -> None:
        """Class initialisation steps.

        :param config_path: Optional path to config file
        """
>>>>>>> main
        self.config_path = pathlib.Path(config_path)
        self.config = self._load_config()

    # ------------------------------------------------------------------
    # Configuration handling
    # ------------------------------------------------------------------

    def _load_config(self) -> AWLConfig:
<<<<<<< HEAD
=======
        """Load the configuration."""
>>>>>>> main
        if not self.config_path.exists():
            return AWLConfig()

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
<<<<<<< HEAD
            # we have some problems reading the configuration so do it again
            print(
                f"Error {exc} loading the configuration, going for a fresh one!")
            return AWLConfig()

        except OSError as exc:
=======
            # if we have some problems parsing the configuration do it again
            print(
                f"Error {exc} loading the configuration, going for a fresh one!")
            return AWLConfig()
        except OSError as exc:
            # go out if we have disk problems
>>>>>>> main
            raise RuntimeError(f"Failed to read configuration: {exc}") from exc

        return AWLConfig(
            api_url=data.get("API_URL", AWLConfig.api_url),
            streets_endpoint=data.get("STR_URL", AWLConfig.streets_endpoint),
            waste_bins=data.get("WASTE_BINS", AWLConfig().waste_bins),
            strasse_nummer=data.get("strasseNummer"),
            strasse_bezeichnung=data.get("strasseBezeichnung"),
        )

    def save_config(self) -> None:
        """Save the configuration."""
        payload = {
            "API_URL": self.config.api_url,
            "STR_URL": self.config.streets_endpoint,
            "WASTE_BINS": self.config.waste_bins,
            "strasseNummer": self.config.strasse_nummer,
            "strasseBezeichnung": self.config.strasse_bezeichnung,
        }
<<<<<<< HEAD
        self.config_path.write_text(json.dumps(
            payload, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # API interaction
    # ------------------------------------------------------------------

    def _get(self, endpoint: str) -> list[dict]:
        """Get data from the endpoint."""
        url = f"{self.config.api_url}{endpoint}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise RuntimeError("Expected list from AWL API")
        return data

    def fetch_streets(self) -> list[dict]:
        """Fetch the all streets from the AWL portal."""
        return self._get(self.config.streets_endpoint)

=======
        self.config_path.write_text(json.dumps(payload, indent=2),
                                    encoding="utf-8")

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _validate_selection(self, entry: str, labels: Iterable[str]) -> None:
        entry_normalized = entry.strip().lower()
        if not any(label.lower() == entry_normalized for label in labels):
            raise ValueError(
                "Entered street name is not in the available list")

    def filter_pickups_by_bins(self, pickups: dict, bins: list[str]) -> dict:
        """Return a dict of pickup dates filtered by bin types."""
        filtered: dict = {}
        requested = set(bins)

        for month, days in pickups.items():
            filtered_days: dict = {}
            for day, day_bins in days.items():
                kept = [b for b in day_bins if b in requested]
                if kept:
                    filtered_days[day] = kept
            if filtered_days:
                filtered[month] = filtered_days
        return filtered

    def filter_next_available_day(self, pickups):
        """Return the next available pickup date from the pickups dict."""
        # Parse the current date
        # go back one day to include today if pickup is later today
        current_date = datetime.now()
        current_year = current_date.year
        # current month is 0-based in the API, so we need to adjust it
        current_month = current_date.month - 1
        current_day = current_date.day

        next_pickup = None
        next_date = None

        # Iterate through the months and years in the dictionary
        for month_year, days in pickups.items():
            month, year = map(int, month_year.split('-'))

            # Skip past months/years
            if year < current_year or (year == current_year and month < current_month):
                continue

            # Check days in the current or future month
            for day, items in days.items():
                day = int(day)
                # Create a datetime object for the pickup date (adjust month back to 1-based)
                pickup_date = datetime(year, month + 1, day)

                # Skip past days in the current month
                if pickup_date < current_date:
                    continue

                # Update the next pickup if it's earlier than the current next_date
                if next_date is None or pickup_date < next_date:
                    next_date = pickup_date
                    next_pickup = {f"{month}-{year}": {str(day): items}}

        return next_pickup
# ------------------------------------------------------------------
    # API interaction
    # ------------------------------------------------------------------

    def _get(self, endpoint=None, args=None) -> list[dict]:
        """Get data from the endpoint."""
        url = f"{self.config.api_url}"
        if endpoint:
            url = f"{url}{endpoint}"
        if args:
            response = requests.get(url,  params=args, timeout=30)
        else:
            response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, (list, dict)):
            raise RuntimeError("Expected list or dict from AWL API")

        return data

    def fetch_streets(self) -> list[dict]:
        """Fetch all streets from the AWL portal."""
        return self._get(self.config.streets_endpoint)

    def fetch_pickups(self, args=None) -> list[dict]:
        """Use the _get API call to fetch pickups."""
        if not args:
            raise RuntimeError("Error at fetch_pickups: no arguments passed")
        return self._get(args=args)

>>>>>>> main
    # ------------------------------------------------------------------
    # Interactive workflow
    # ------------------------------------------------------------------
    def filter_streets(self, query: str, streets: Sequence[dict]) -> List[dict]:
<<<<<<< HEAD
        """Filter out the street from a list of streets and return the lower representation."""
        query_lower = query.lower()
        return [street for street in streets if query_lower in street["strasseBezeichnung"].lower()]

    def draw_menu(self, stdscr, query: str, filtered: Sequence[dict], highlight_idx: int) -> None:
=======
        """Search street from a list of streets."""
        query_lower = query.lower()
        return [street for street in streets
                if query_lower in street["strasseBezeichnung"].lower()]

    def draw_menu(self, stdscr, query: str,
                  filtered: Sequence[dict],
                  highlight_idx: int) -> None:
>>>>>>> main
        """Draw a menu to select a street."""
        stdscr.clear()
        max_y, _ = stdscr.getmaxyx()

<<<<<<< HEAD
        stdscr.addstr(0, 0, "Type to filter cities (ESC to quit)")
        stdscr.addstr(1, 0, f"> {query}")
        stdscr.addstr(2, 0, "Results:")

        for idx, city in enumerate(filtered[: max_y - 4]):
            line = f"  {city['strasseBezeichnung']}"
=======
        stdscr.addstr(0, 0, "Type to filter street (ESC to quit)")
        stdscr.addstr(1, 0, f"> {query}")
        stdscr.addstr(2, 0, "Results:")

        for idx, street in enumerate(filtered[: max_y - 4]):
            line = f"  {street['strasseBezeichnung']}"
>>>>>>> main
            if idx == highlight_idx:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(3 + idx, 0, line)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(3 + idx, 0, line)

        if not filtered:
            stdscr.addstr(3, 0, "  No matches")

        stdscr.refresh()

    def select_street(self, stdscr, streets: Sequence[dict]) -> dict | None:
        """Select a street from a list of streets."""
        query = ""
        filtered = list(streets)
        highlight_idx = 0

        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.keypad(True)

        while True:
            self.draw_menu(stdscr, query, filtered, highlight_idx)
            key = stdscr.getch()

            if key in (curses.KEY_EXIT, 27):  # ESC
                return None
            if key in (curses.KEY_ENTER, 10, 13):
                if filtered:
                    return filtered[highlight_idx]
                continue

            if key in (curses.KEY_BACKSPACE, 127, 8):
                query = query[:-1]
            elif key == curses.KEY_DOWN:
                if filtered:
                    highlight_idx = (highlight_idx + 1) % len(filtered)
            elif key == curses.KEY_UP:
                if filtered:
                    highlight_idx = (highlight_idx - 1) % len(filtered)
            elif 32 <= key <= 126:
                query += chr(key)

            filtered = self.filter_streets(query, streets)
            if filtered:
                highlight_idx %= len(filtered)
            else:
                highlight_idx = 0

<<<<<<< HEAD
    def ensure_street_selected(self, select_fn=None, input_fn=None) -> None:
        """Ensure configuration contains a street selection.

        :param select_fn: Optional callable to present a selection UI.
            It receives the list of street labels and returns the chosen index.
        :param input_fn: Optional callable to obtain textual user input.
        """

        if self.config.is_complete:
            return

        streets = self.fetch_streets()
#        labels = [s.get("strasseBezeichnung", "") for s in streets]
#
#        if select_fn is None:
#            select_fn = self._default_select_fn
#        if input_fn is None:
#            input_fn = self._default_input_fn
#
#        selected_index = select_fn(labels)
#        manual_entry = input_fn("Enter the street name for verification: ")
#
#        self._validate_selection(manual_entry, labels)
#
#        selected_street = streets[selected_index]
#        self.config.strasse_nummer = selected_street.get("strasseNummer")
#        self.config.strasse_bezeichnung = selected_street.get("strasseBezeichnung")

        def runner(stdscr):
            # selection = select_city(stdscr, CITIES)
            selection = self.select_street(stdscr, streets)
            stdscr.clear()
            if selection:
                stdscr.addstr(
                    0, 0, f"You selected: {selection['strasseBezeichnung']}")
                self.config.strasse_nummer = selection["strasseNummer"]
                self.config.strasse_bezeichnung = selection["strasseBezeichnung"]
            else:
                stdscr.addstr(0, 0, "No selection made")
                raise RuntimeError(f"No street selected")
            stdscr.refresh()
            stdscr.getch()
=======
    def ensure_correct_street(self) -> None:
        """Ensure configuration contains a street selection."""
        # do we have a complete configuration already? if yes we are done
        if self.config.is_complete:
            return

        # get all streets via API
        streets = self.fetch_streets()

        def runner(stdscr):
            # selection = select_city(stdscr, CITIES)
            key = ""
            while key not in (ord('y'), ord('Y')):
                selection = self.select_street(stdscr, streets)
                stdscr.clear()
                if selection:
                    stdscr.addstr(
                        0, 0, f"You selected: {selection['strasseBezeichnung']}")
                    stdscr.addstr(1, 0, "Is this correct (Y/N)")
                    stdscr.refresh()
                    key = stdscr.getch()
                else:
                    stdscr.addstr(0, 0, "No selection made")
                    raise RuntimeError("No street selected")
                stdscr.refresh()
            # stdscr.getch()
            self.config.strasse_nummer = selection["strasseNummer"]
            self.config.strasse_bezeichnung = selection["strasseBezeichnung"]
>>>>>>> main

        curses.wrapper(runner)

        self.save_config()

<<<<<<< HEAD
    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _validate_selection(self, entry: str, labels: Iterable[str]) -> None:
        entry_normalized = entry.strip().lower()
        if not any(label.lower() == entry_normalized for label in labels):
            raise ValueError(
                "Entered street name is not in the available list")

    @staticmethod
    def _default_select_fn(labels: List[str]) -> int:
        for idx, label in enumerate(labels):
            print(f"[{idx}] {label}")
        while True:
            raw = input("Select the street index: ")
            if raw.isdigit():
                chosen = int(raw)
                if 0 <= chosen < len(labels):
                    return chosen
            print("Invalid selection, try again.")

    @staticmethod
    def _default_input_fn(prompt: str) -> str:
        return input(prompt)

    # ------------------------------------------------------------------
    # Select Street from list of strees
    # ------------------------------------------------------------------


def main() -> None:
    """Sample workflow demonstrating how to use AWLScheduleClient."""

    client = AWLScheduleClient()

    # Ensure a street configuration exists (prompts user if needed)
    client.ensure_street_selected()

    # Placeholder for future steps: e.g., fetch next garbage pickup dates
    print(
        "Configured street:",
        client.config.strasse_bezeichnung,
        f"(ID: {client.config.strasse_nummer})",
    )
    print("TODO: Call additional API endpoints to retrieve pickup schedule.")
=======
    def get_next_pickup_date(self, bins=None):
        """Get the next pickup date."""
        if not bins:
            # no bins select get all
            bins = self.config.waste_bins

        # get pickups for this month
        pickups = self.get_pickup_dates(scope="m", bins=bins)
        # select the next pickup date from the pickups dict
        return self.filter_next_available_day(pickups)

    def get_pickup_dates(self, scope="m", bins: Optional[list] = None):
        """Get AWL waste bin pickup dates.

        param: range: Optional
                "m"  - (default) - get pickups for the current month
                "3m" - 3 months range
                "y"  - get all dates for this year
        param: bins: Optional
                type of config.waste_bins
        """
        # arguments for the API call
        args = {
            "streetNum": self.config.strasse_nummer,
            "homeNumber": "1",  # not used anyway
            "startMonth": datetime.now().strftime('%b %Y')
        }

        if scope == "3m":
            args["isYear"] = "false"
            args["isTreeMonthRange"] = "true"
        elif scope == "y":
            args["isYear"] = "true"
            args["isTreeMonthRange"] = "false"
        else:
            args["isYear"] = "false"
            args["isTreeMonthRange"] = "false"

        pickups = self._get(args=args)

        # no bins specified we will use all and return directly
        if not bins:
            bins = self.config.waste_bins
            return pickups

        if not set(bins).issubset(set(self.config.waste_bins)):
            invl_bins = [
                item for item in bins if item not in self.config.waste_bins]
            print(f"Warning: {invl_bins} is not a valid waste type")

        return self.filter_pickups_by_bins(pickups, bins)


# ------------------------------------------------------------------
# The main program loop starts here
# ------------------------------------------------------------------
def main() -> None:
    """Program main loop."""
    ap = argparse.ArgumentParser()
    ap.add_argument('-c', '--config',
                    required=False,
                    default='awl.conf',
                    help='configuration file to use')
    args = ap.parse_args()
    # print(f"arguments {args}")
    # initialize the class and read the config
    client = AWLScheduleClient(args.config)

    # Ensure a street configuration exists (prompts user if needed)
    client.ensure_correct_street()

    # Get pickup dates
    pickup_dates = client.get_pickup_dates(scope='m',
                                           bins=["pink",
                                                 "gelb",
                                                 "blau"])
    # print the results
    for month, days in pickup_dates.items():
        print(f"Month: {month}")
        for day, bins in days.items():
            print(f"{day} : {bins}")

    next_pickup = client.get_next_pickup_date(bins=["gelb"])
    print("Next pickup:", next_pickup)

    # Placeholder for future steps: e.g., fetch next garbage pickup dates
    # print(
    #    "Configured street:",
    #    client.config.strasse_bezeichnung,
    #    f"(ID: {client.config.strasse_nummer})",
    # )
    # print("TODO: Call additional API endpoints to retrieve pickup schedule.")
>>>>>>> main


if __name__ == "__main__":
    main()
