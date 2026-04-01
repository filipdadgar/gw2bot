"""Records player harvest positions from MumbleLink to build real farming routes.

Usage flow:
  1. Call start() to begin a recording session.
  2. Each time the player harvests a node, call record_position(mumble_data).
     The position is added as a waypoint only if it is far enough from the
     previous one (MIN_WAYPOINT_DISTANCE game units).
  3. Call stop_and_save() to persist the waypoints as a route file and get back
     the new route_id.  Returns None if fewer than 2 waypoints were recorded.
  4. Call discard() instead to throw away the session without saving.

Waypoints are stored in GW2 world-space coordinates (metres).  The route_builder
also persists the continent coordinates so the orchestrator can use whichever
system is more convenient for navigation.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.adapters.mumble_link_reader import MumbleLinkData
    from src.core.persistence.storage import Storage

logger = logging.getLogger(__name__)

# Minimum Euclidean distance (world units / metres) between consecutive
# waypoints.  Keeps the route from being cluttered with near-duplicate points
# when the player pauses or harvests multiple nodes in the same spot.
MIN_WAYPOINT_DISTANCE: float = 15.0

# Minimum number of waypoints required before a route is considered valid.
MIN_WAYPOINTS_TO_SAVE: int = 2


@dataclass
class RecordedWaypoint:
    x: float          # world-space X (east/west)
    y: float          # world-space Y (vertical — kept for reference)
    z: float          # world-space Z (north/south)
    cx: float         # continent-coord X (matches minimap)
    cy: float         # continent-coord Y
    map_id: int
    timestamp: float = field(default_factory=time.monotonic)


@dataclass
class RecordingStatus:
    recording: bool
    waypoint_count: int
    map_id: int


class RouteRecorder:
    """Accumulates player positions during manual harvesting into a route.

    Thread-safe: record_position() is called from the input listener thread
    while status() may be polled from the API thread.
    """

    def __init__(self, storage: "Storage") -> None:
        self._storage = storage
        self._lock = threading.Lock()
        self._waypoints: list[RecordedWaypoint] = []
        self._recording = False
        self._session_map_id = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def recording(self) -> bool:
        return self._recording

    def status(self) -> RecordingStatus:
        with self._lock:
            return RecordingStatus(
                recording=self._recording,
                waypoint_count=len(self._waypoints),
                map_id=self._session_map_id,
            )

    def start(self) -> None:
        """Begin a new recording session, discarding any previous data."""
        with self._lock:
            self._waypoints = []
            self._recording = True
            self._session_map_id = 0
        logger.info("route_recording_started")

    def record_position(self, data: "MumbleLinkData") -> bool:
        """Add current player position as a waypoint if valid and far enough.

        Returns True when a new waypoint was appended.
        """
        if not self._recording or not data.available:
            return False

        with self._lock:
            # Lock the session to the first map seen so teleports don't
            # create cross-map routes.
            if self._session_map_id == 0:
                self._session_map_id = data.map_id
            elif data.map_id != self._session_map_id:
                logger.debug("route_recorder_map_change_ignored")
                return False

            if self._waypoints:
                last = self._waypoints[-1]
                dx = data.avatar_x - last.x
                dz = data.avatar_z - last.z
                dist = (dx * dx + dz * dz) ** 0.5
                if dist < MIN_WAYPOINT_DISTANCE:
                    return False

            wp = RecordedWaypoint(
                x=data.avatar_x,
                y=data.avatar_y,
                z=data.avatar_z,
                cx=data.continent_x,
                cy=data.continent_y,
                map_id=data.map_id,
            )
            self._waypoints.append(wp)
            logger.info("waypoint_recorded index=%d x=%.1f z=%.1f", len(self._waypoints) - 1, wp.x, wp.z)
            return True

    def stop_and_save(self) -> str | None:
        """Stop recording and persist the route.  Returns route_id or None."""
        with self._lock:
            self._recording = False
            waypoints = list(self._waypoints)
            map_id = self._session_map_id

        if len(waypoints) < MIN_WAYPOINTS_TO_SAVE:
            logger.warning(
                "route_recording_too_few_waypoints count=%d min=%d",
                len(waypoints),
                MIN_WAYPOINTS_TO_SAVE,
            )
            return None

        # Persist using the existing RouteBuilder so route files stay consistent.
        from src.core.discovery.route_builder import RouteBuilder

        builder = RouteBuilder(self._storage)
        serialised = [
            {
                "x": round(wp.x, 2),
                "y": round(wp.z, 2),   # store Z as "y" — the orchestrator uses (x,y) pairs
                "world_y": round(wp.y, 2),
                "continent_x": round(wp.cx, 2),
                "continent_y": round(wp.cy, 2),
                "map_id": wp.map_id,
            }
            for wp in waypoints
        ]
        route_id = builder.persist_route(waypoints=serialised, map_id=map_id)
        logger.info("route_saved route_id=%s waypoints=%d map_id=%d", route_id, len(waypoints), map_id)
        return route_id

    def discard(self) -> None:
        """Abandon the current session without saving."""
        with self._lock:
            self._recording = False
            self._waypoints = []
        logger.info("route_recording_discarded")
