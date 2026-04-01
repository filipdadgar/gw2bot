"""GW2 MumbleLink reader — real-time player position, facing, and mount state.

GW2 writes into a Windows named shared-memory block called 'MumbleLink' every
game tick.  No extra permissions or addons are required; it is part of the base
game's API.  Full spec: https://wiki.guildwars2.com/wiki/API:MumbleLink

Memory layout (5460 bytes total):
  Offset   Size   Field
  0        4      uiVersion   (uint32)
  4        4      uiTick      (uint32, increments every game tick ~50 ms)
  8        12     fAvatarPosition  float[3]  world-space meters (x, y_up, z)
  20       12     fAvatarFront     float[3]  unit facing vector
  32       12     fAvatarTop       float[3]
  44       512    name             wchar_t[256]  app name ("Guild Wars 2")
  556      12     fCameraPosition  float[3]
  568      12     fCameraFront     float[3]
  580      12     fCameraTop       float[3]
  592      512    identity         wchar_t[256]  JSON: map_id, profession, etc.
  1104     4      context_len      uint32
  1108     256    context          GW2-specific struct (see GW2Context below)
  1364     4096   description      wchar_t[2048]

GW2Context (context bytes starting at offset 1108):
  0    28   serverAddress  (bytes)
  28   4    mapId          uint32
  32   4    mapType        uint32
  36   4    shardId        uint32
  40   4    instance       uint32
  44   4    buildId        uint32
  48   4    uiState        uint32  (flags)
  52   2    compassWidth   uint16
  54   2    compassHeight  uint16
  56   4    compassRotation float
  60   4    playerX        float  (continent coordinates)
  64   4    playerY        float  (continent coordinates)
  68   4    mapCenterX     float
  72   4    mapCenterY     float
  76   4    mapScale       float
  80   4    processId      uint32
  84   1    mountIndex     uint8  (0=none,1=Jackal,2=Griffon,3=Springer,
                                   4=Skimmer,5=Raptor,6=RollerBeetle,
                                   7=Warclaw,8=Skyscale,9=SiegeTurtle,
                                   10=SkyFin)
"""

from __future__ import annotations

import json
import logging
import mmap
import struct
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

_MUMBLE_SIZE = 5460

# Key byte offsets
_OFF_TICK = 4
_OFF_AVATAR_POS = 8       # float x, y_up, z
_OFF_AVATAR_FRONT = 20    # float fx, fy, fz
_OFF_IDENTITY = 592       # wchar_t[256] — JSON string
_WCHAR256 = 256 * 2       # bytes
_OFF_CONTEXT = 1108       # GW2Context starts here

# Within GW2Context
_CTX_MAP_ID = 28
_CTX_PLAYER_X = 60        # continent coords
_CTX_PLAYER_Y = 64
_CTX_MAP_SCALE = 76
_CTX_MOUNT_INDEX = 84

MOUNT_NAMES = {
    0: "none",
    1: "Jackal",
    2: "Griffon",
    3: "Springer",
    4: "Skimmer",
    5: "Raptor",
    6: "RollerBeetle",
    7: "Warclaw",
    8: "Skyscale",
    9: "SiegeTurtle",
    10: "SkyFin",
}


@dataclass
class MumbleLinkData:
    """Snapshot of GW2 player state read from MumbleLink shared memory."""

    tick: int = 0

    # World-space position in metres (GW2 engine units).
    # x = east/west, y = up/down (vertical), z = north/south.
    avatar_x: float = 0.0
    avatar_y: float = 0.0
    avatar_z: float = 0.0

    # Unit vector pointing out of the avatar's eyes (camera-independent).
    front_x: float = 0.0
    front_z: float = 0.0

    # Continent-coordinate position (matches minimap / GW2 cartography API).
    continent_x: float = 0.0
    continent_y: float = 0.0
    map_scale: float = 1.0

    # GW2-specific state
    map_id: int = 0
    mount_index: int = 0   # 0 = on foot, >0 = mounted (see MOUNT_NAMES)

    available: bool = False

    @property
    def is_mounted(self) -> bool:
        return self.mount_index > 0

    @property
    def mount_name(self) -> str:
        return MOUNT_NAMES.get(self.mount_index, f"mount_{self.mount_index}")


class MumbleLinkReader:
    """Open and read GW2's MumbleLink shared memory block.

    GW2 must be running for data to be meaningful.  When GW2 is not running
    the shared memory may not exist (open fails) or the tick counter stays at 0.
    All errors are caught and surfaced as MumbleLinkData(available=False).
    """

    SHARED_MEM_NAME = "MumbleLink"

    def __init__(self) -> None:
        self._mmap: mmap.mmap | None = None
        self._available = False
        self._last_tick = -1
        self._try_open()

    def _try_open(self) -> None:
        try:
            self._mmap = mmap.mmap(
                -1,
                _MUMBLE_SIZE,
                tagname=self.SHARED_MEM_NAME,
                access=mmap.ACCESS_READ,
            )
            self._available = True
            logger.info("mumble_link_opened")
        except Exception as exc:
            logger.warning("mumble_link_unavailable: %s", exc)
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def read(self) -> MumbleLinkData:
        """Return the latest MumbleLink snapshot, or an unavailable stub.

        If the reader was never successfully opened (e.g. bot started before
        GW2), this retries the open on every call so it connects automatically
        once GW2 launches.
        """
        if not self._available or self._mmap is None:
            self._try_open()          # retry — GW2 may have started since boot
        if not self._available or self._mmap is None:
            return MumbleLinkData(available=False)

        try:
            self._mmap.seek(0)
            raw = self._mmap.read(_MUMBLE_SIZE)
        except Exception:
            logger.exception("mumble_link_read_error")
            return MumbleLinkData(available=False)

        tick = struct.unpack_from("<I", raw, _OFF_TICK)[0]

        # tick==0 almost always means GW2 is not in a loaded map yet
        if tick == 0:
            return MumbleLinkData(available=False)

        ax, ay, az = struct.unpack_from("<fff", raw, _OFF_AVATAR_POS)
        fx, _fy, fz = struct.unpack_from("<fff", raw, _OFF_AVATAR_FRONT)

        # Parse identity JSON for map_id
        id_bytes = raw[_OFF_IDENTITY: _OFF_IDENTITY + _WCHAR256]
        try:
            id_str = id_bytes.decode("utf-16-le").rstrip("\x00")
            identity: dict[str, Any] = json.loads(id_str) if id_str.strip() else {}
        except Exception:
            identity = {}

        map_id_from_identity = int(identity.get("map_id", 0))

        # Parse GW2Context for mount, continent coords, map_id (more reliable)
        ctx = raw[_OFF_CONTEXT:]
        try:
            map_id_ctx = struct.unpack_from("<I", ctx, _CTX_MAP_ID)[0]
            cx = struct.unpack_from("<f", ctx, _CTX_PLAYER_X)[0]
            cy = struct.unpack_from("<f", ctx, _CTX_PLAYER_Y)[0]
            scale = struct.unpack_from("<f", ctx, _CTX_MAP_SCALE)[0]
            mount_idx = struct.unpack_from("<B", ctx, _CTX_MOUNT_INDEX)[0]
        except Exception:
            map_id_ctx = map_id_from_identity
            cx = cy = 0.0
            scale = 1.0
            mount_idx = 0

        map_id = map_id_ctx if map_id_ctx else map_id_from_identity

        return MumbleLinkData(
            tick=tick,
            avatar_x=ax,
            avatar_y=ay,
            avatar_z=az,
            front_x=fx,
            front_z=fz,
            continent_x=cx,
            continent_y=cy,
            map_scale=scale,
            map_id=map_id,
            mount_index=mount_idx,
            available=True,
        )

    def close(self) -> None:
        if self._mmap is not None:
            try:
                self._mmap.close()
            except Exception:
                pass
            self._mmap = None
        self._available = False
