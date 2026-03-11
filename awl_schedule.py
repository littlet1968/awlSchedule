#!/usr/bin/env python3
"""Client for retrieving AWL garbage pickup information.

This module encapsulates the workflow described in ``awlSchedule.md``.
It handles configuration management, discovery of available streets
via the AWL API, and persistence of the selected street configuration.
"""

from __future__ import annotations

import curses
import json
import argparse
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
        """Check that the configuration is OK."""
        return bool(self.strasse_nummer and self.strasse_bezeichnung)


class AWLScheduleClient:
    """High-level client orchestrating configuration and street selection."""

    def __init__(self, config_path: str | pathlib.Path = "awl.conf") -> None:
        """Class initialisation steps.

        :param config_path: Optional path to config file
        """
        self.config_path = pathlib.Path(config_path)
        self.config = self._load_config()

    # ------------------------------------------------------------------
    # Configuration handling
    # ------------------------------------------------------------------

    def _load_config(self) -> AWLConfig:
        """Load the configuration."""
        if not self.config_path.exists():
            return AWLConfig()

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            # if we have some problems parsing the configuration do it again
            print(
                f"Error {exc} loading the configuration, going for a fresh one!")
            return AWLConfig()
        except OSError as exc:
            # go out if we have disk problems
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

    def fetch_pickups(self, date=None, bins=None) -> list[dict]:
        """Use the _get API call to fetch pickups."""
        return

    # ------------------------------------------------------------------
    # Interactive workflow
    # ------------------------------------------------------------------
    def filter_streets(self, query: str, streets: Sequence[dict]) -> List[dict]:
        """Search street from a list of streets."""
        query_lower = query.lower()
        return [street for street in streets
                if query_lower in street["strasseBezeichnung"].lower()]

    def draw_menu(self, stdscr, query: str,
                  filtered: Sequence[dict],
                  highlight_idx: int) -> None:
        """Draw a menu to select a street."""
        stdscr.clear()
        max_y, _ = stdscr.getmaxyx()

        stdscr.addstr(0, 0, "Type to filter cities (ESC to quit)")
        stdscr.addstr(1, 0, f"> {query}")
        stdscr.addstr(2, 0, "Results:")

        for idx, city in enumerate(filtered[: max_y - 4]):
            line = f"  {city['strasseBezeichnung']}"
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

        curses.wrapper(runner)

        self.save_config()

    def get_next_pickup_date(self, bins=None):
        """Get the next pickup date."""
        if not bins:
            # no bins select get all
            bins = self.config.waste_bins

        pickups = self.fetch_pickups(bins)
        return

# ------------------------------------------------------------------
# The main program starts here
# ------------------------------------------------------------------


def main() -> None:
    """Program main loop."""
    ap = argparse.ArgumentParser()
    ap.add_argument('-c', '--config',
                    required=False,
                    default='awl.conf',
                    help='configuration file to use')
    args = ap.parse_args()
    print(f"arguments {args}")
    client = AWLScheduleClient(args.config)

    # Ensure a street configuration exists (prompts user if needed)
    client.ensure_street_selected()

    # Placeholder for future steps: e.g., fetch next garbage pickup dates
    print(
        "Configured street:",
        client.config.strasse_bezeichnung,
        f"(ID: {client.config.strasse_nummer})",
    )
    print("TODO: Call additional API endpoints to retrieve pickup schedule.")


if __name__ == "__main__":
    main()
