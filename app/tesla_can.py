"""
Tesla Local Control — CAN Bus Driver for 2015 Model S 85D
==========================================================
Communicates with Body CAN (BCAN) at 125 kbps via OBD-II port.
Handles: lock/unlock, frunk, trunk, windows, lights, horn,
         charge port, HVAC, mirrors, interior lights.
Reads: battery SOC, gear, speed, drive mode, charge port state,
       door/window states, temperatures.
"""

import can
import logging
import time
import threading
from typing import Optional

log = logging.getLogger("tesla_can")

# ── CAN Configuration ────────────────────────────────────────────────
CAN_INTERFACE = "socketcan"
CAN_CHANNEL   = "can0"
CAN_BITRATE   = 125000  # Body CAN

# ── CAN IDs for Model S (pre-2021 Body CAN) ──────────────────────────
# ⚠️ Community-documented. Your car may differ.
#    Use the CAN Sniffer to verify: python3 tools/can_sniffer.py
# ── Control IDs ──
CAN_ID_DOOR_LOCK      = 0x216
CAN_ID_FRONT_TRUNK    = 0x217
CAN_ID_REAR_TRUNK     = 0x218
CAN_ID_WINDOWS        = 0x215
CAN_ID_LIGHTS         = 0x244
CAN_ID_HORN           = 0x245
CAN_ID_CHARGE_PORT    = 0x312
CAN_ID_HVAC           = 0x302
CAN_ID_MIRRORS        = 0x210
CAN_ID_INTERIOR_LIGHT = 0x240

# ── Status IDs (read from CAN bus) ──
CAN_ID_DRIVE_MODE    = 0x102
CAN_ID_BATTERY_SOC   = 0x202
CAN_ID_SPEED         = 0x212
CAN_ID_GEAR          = 0x222
CAN_ID_CHARGE_STATE  = 0x312  # also carries status
CAN_ID_HVAC_STATUS   = 0x302
CAN_ID_TEMP_AMBIENT  = 0x304
CAN_ID_DOOR_STATE    = 0x216  # response frames
CAN_ID_WINDOW_STATE  = 0x215

# ── Command Payloads ─────────────────────────────────────────────────
CMD_LOCK           = bytes([0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01])
CMD_UNLOCK         = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_FRUNK          = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_TRUNK          = bytes([0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_LIGHTS         = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # flash
CMD_LIGHTS_OFF     = bytes([0x00] * 8)
CMD_HORN           = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_WINDOW_CLOSE   = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_WINDOW_VENT    = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_CHARGE_OPEN    = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_CHARGE_CLOSE   = bytes([0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_MIRRORS_FOLD   = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_MIRRORS_UNFOLD = bytes([0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_INTERIOR_ON    = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_INTERIOR_OFF   = bytes([0x00] * 8)
CMD_HVAC_ON        = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_HVAC_OFF       = bytes([0x00] * 8)

# ── Decode Maps ──────────────────────────────────────────────────────
GEAR_MAP = {0: "P", 1: "R", 2: "N", 3: "D"}
DRIVE_MODE_MAP = {0: "POWER_SAVE", 1: "CHILL", 2: "SPORT", 3: "INSANE"}
CHARGE_PORT_MAP = {0: "CLOSED", 1: "OPENING", 2: "OPEN", 3: "LOCKED"}
DOOR_MAP = {0: "CLOSED", 1: "OPEN"}


class TeslaCANDriver:
    """CAN bus driver for 2015 Tesla Model S."""

    def __init__(self):
        self._bus: Optional[can.BusABC] = None
        self._lock = threading.Lock()
        self._status = {"connected": False}
        self._running = False
        self._listener: Optional[threading.Thread] = None

    # ── Bus Lifecycle ────────────────────────────────────────────────

    def connect(self) -> bool:
        """Open CAN bus connection."""
        try:
            self._bus = can.interface.Bus(
                channel=CAN_CHANNEL,
                bustype=CAN_INTERFACE,
                bitrate=CAN_BITRATE,
            )
            self._running = True
            self._status["connected"] = True
            log.info(f"✅ CAN connected: {CAN_CHANNEL} @ {CAN_BITRATE}")
            self._listener = threading.Thread(target=self._listen, daemon=True)
            self._listener.start()
            return True
        except Exception as e:
            log.error(f"❌ CAN connect failed: {e}")
            self._status["connected"] = False
            return False

    def disconnect(self):
        self._running = False
        if self._bus:
            self._bus.shutdown()
            self._bus = None
        self._status["connected"] = False

    @property
    def is_connected(self) -> bool:
        return self._bus is not None and self._status.get("connected", False)

    # ── Status Decoders ──────────────────────────────────────────────

    @staticmethod
    def _decode_gear(data: bytes) -> Optional[str]:
        if len(data) >= 1:
            return GEAR_MAP.get(data[0], f"UNKNOWN({data[0]})")
        return None

    @staticmethod
    def _decode_drive_mode(data: bytes) -> Optional[str]:
        if len(data) >= 1:
            return DRIVE_MODE_MAP.get(data[0], f"UNKNOWN({data[0]})")
        return None

    @staticmethod
    def _decode_speed(data: bytes) -> Optional[float]:
        """Speed in km/h. Common encoding: bytes 4-5 as uint16."""
        if len(data) >= 6:
            raw = (data[4] << 8) | data[5]
            return round(raw / 100.0, 1) if raw else 0.0
        return None

    @staticmethod
    def _decode_soc(data: bytes) -> Optional[int]:
        """Battery state of charge, byte 0 = percentage."""
        if len(data) >= 1:
            return data[0]
        return None

    @staticmethod
    def _decode_charge_port(data: bytes) -> dict:
        """Charge port + charging status."""
        result = {"state": "UNKNOWN", "charging": False}
        if len(data) >= 1:
            result["state"] = CHARGE_PORT_MAP.get(data[0], f"UNKNOWN({data[0]})")
            result["charging"] = data[0] in (3,)
        return result

    @staticmethod
    def _decode_temperature(data: bytes) -> Optional[float]:
        """Temperature in Celsius from byte 0."""
        if len(data) >= 1:
            return float(data[0])
        return None

    @staticmethod
    def _decode_door_state(data: bytes) -> dict:
        """
        Door lock state — individual door open/close.
        Common: byte 0 = driver, byte 1 = passenger,
                byte 2 = rear left, byte 3 = rear right
        """
        if len(data) < 4:
            return {"driver": None, "passenger": None, "rear_left": None, "rear_right": None}
        return {
            "driver": DOOR_MAP.get(data[0] & 1, "?"),
            "passenger": DOOR_MAP.get(data[1] & 1, "?"),
            "rear_left": DOOR_MAP.get(data[2] & 1, "?"),
            "rear_right": DOOR_MAP.get(data[3] & 1, "?"),
            "locked": data[0] == 0x01,  # guess: 0x01 bytes = locked
        }

    @staticmethod
    def _decode_window_state(data: bytes) -> Optional[str]:
        """Window position. 0x00 = closed, 0x01..0xFF = vent position."""
        if len(data) >= 1:
            if data[0] == 0x00:
                return "CLOSED"
            return "VENTED"
        return None

    # ── Background Listener ──────────────────────────────────────────

    KNOWN_STATUS_IDS = {
        CAN_ID_DRIVE_MODE:     "drive_mode_raw",
        CAN_ID_BATTERY_SOC:    "battery_soc_raw",
        CAN_ID_SPEED:          "speed_raw",
        CAN_ID_GEAR:           "gear_raw",
        CAN_ID_CHARGE_STATE:   "charge_port_raw",
        CAN_ID_HVAC_STATUS:    "hvac_raw",
        CAN_ID_TEMP_AMBIENT:   "ambient_temp_raw",
        CAN_ID_DOOR_STATE:     "door_state_raw",
        CAN_ID_WINDOW_STATE:   "window_state_raw",
    }

    def _listen(self):
        """Listen for status messages from the car."""
        while self._running and self._bus:
            try:
                msg = self._bus.recv(timeout=0.3)
                if msg and msg.arbitration_id in self.KNOWN_STATUS_IDS:
                    with self._lock:
                        self._status[self.KNOWN_STATUS_IDS[msg.arbitration_id]] = msg.data
            except Exception:
                if self._running:
                    time.sleep(0.5)

    def get_status(self) -> dict:
        """Return decoded vehicle status."""
        with self._lock:
            soc_raw = self._status.get("battery_soc_raw", b'')
            gear_raw = self._status.get("gear_raw", b'')
            speed_raw = self._status.get("speed_raw", b'')
            drive_raw = self._status.get("drive_mode_raw", b'')
            charge_raw = self._status.get("charge_port_raw", b'')
            door_raw = self._status.get("door_state_raw", b'')
            window_raw = self._status.get("window_state_raw", b'')
            ambient_raw = self._status.get("ambient_temp_raw", b'')
            hvac_raw = self._status.get("hvac_raw", b'')

        return {
            "connected": self.is_connected,
            "battery_soc": self._decode_soc(soc_raw),
            "gear": self._decode_gear(gear_raw),
            "speed_kmh": self._decode_speed(speed_raw),
            "drive_mode": self._decode_drive_mode(drive_raw),
            "charge_port": self._decode_charge_port(charge_raw),
            "doors": self._decode_door_state(door_raw),
            "windows": self._decode_window_state(window_raw),
            "ambient_temp_c": self._decode_temperature(ambient_raw),
        }

    # ── Send CAN Frame ───────────────────────────────────────────────

    def _send(self, can_id: int, data: bytes) -> bool:
        """Send a CAN frame. Returns True on success."""
        if not self._bus:
            log.warning("CAN bus not connected")
            return False
        msg = can.Message(
            arbitration_id=can_id,
            data=data,
            is_extended_id=False,
        )
        try:
            with self._lock:
                self._bus.send(msg)
            log.info(f"TX: {hex(can_id)} [{len(data)}] {data.hex()}")
            return True
        except Exception as e:
            log.error(f"CAN send error: {e}")
            return False

    # ── High-Level Commands ──────────────────────────────────────────

    def lock(self) -> dict:
        ok = self._send(CAN_ID_DOOR_LOCK, CMD_LOCK)
        return {"success": ok, "command": "lock"}

    def unlock(self) -> dict:
        ok = self._send(CAN_ID_DOOR_LOCK, CMD_UNLOCK)
        return {"success": ok, "command": "unlock"}

    def frunk(self) -> dict:
        ok = self._send(CAN_ID_FRONT_TRUNK, CMD_FRUNK)
        return {"success": ok, "command": "frunk"}

    def trunk(self) -> dict:
        ok = self._send(CAN_ID_REAR_TRUNK, CMD_TRUNK)
        return {"success": ok, "command": "trunk"}

    def flash_lights(self) -> dict:
        ok1 = self._send(CAN_ID_LIGHTS, CMD_LIGHTS)
        time.sleep(0.3)
        ok2 = self._send(CAN_ID_LIGHTS, CMD_LIGHTS_OFF)
        return {"success": ok1 and ok2, "command": "flash"}

    def honk(self) -> dict:
        ok = self._send(CAN_ID_HORN, CMD_HORN)
        return {"success": ok, "command": "honk"}

    def windows_vent(self) -> dict:
        ok = self._send(CAN_ID_WINDOWS, CMD_WINDOW_VENT)
        return {"success": ok, "command": "windows_vent"}

    def windows_close(self) -> dict:
        ok = self._send(CAN_ID_WINDOWS, CMD_WINDOW_CLOSE)
        return {"success": ok, "command": "windows_close"}

    def charge_port_open(self) -> dict:
        ok = self._send(CAN_ID_CHARGE_PORT, CMD_CHARGE_OPEN)
        return {"success": ok, "command": "charge_port_open"}

    def charge_port_close(self) -> dict:
        ok = self._send(CAN_ID_CHARGE_PORT, CMD_CHARGE_CLOSE)
        return {"success": ok, "command": "charge_port_close"}

    def mirrors_fold(self) -> dict:
        ok = self._send(CAN_ID_MIRRORS, CMD_MIRRORS_FOLD)
        return {"success": ok, "command": "mirrors_fold"}

    def mirrors_unfold(self) -> dict:
        ok = self._send(CAN_ID_MIRRORS, CMD_MIRRORS_UNFOLD)
        return {"success": ok, "command": "mirrors_unfold"}

    def interior_lights_on(self) -> dict:
        ok = self._send(CAN_ID_INTERIOR_LIGHT, CMD_INTERIOR_ON)
        return {"success": ok, "command": "interior_lights_on"}

    def interior_lights_off(self) -> dict:
        ok = self._send(CAN_ID_INTERIOR_LIGHT, CMD_INTERIOR_OFF)
        return {"success": ok, "command": "interior_lights_off"}

    def hvac_on(self) -> dict:
        ok = self._send(CAN_ID_HVAC, CMD_HVAC_ON)
        return {"success": ok, "command": "hvac_on"}

    def hvac_off(self) -> dict:
        ok = self._send(CAN_ID_HVAC, CMD_HVAC_OFF)
        return {"success": ok, "command": "hvac_off"}
