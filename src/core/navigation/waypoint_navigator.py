"""Waypoint navigation helpers for discovered route traversal."""

from __future__ import annotations


class WaypointNavigator:
    """Computes waypoint progression for looped routes."""

    def next_index(self, current_index: int, total_waypoints: int) -> int:
        """Return next waypoint index with loop-around behavior."""

        if total_waypoints <= 0:
            return 0
        return (current_index + 1) % total_waypoints
