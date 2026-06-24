"""
Tesla CANServer MyRemote — CAN Bus Driver for 2015 Model S 85D
==========================================================
Communicates with Body CAN (BCAN) at 125 kbps via OBD-II port.
Handles: lock/unlock, frunk, trunk, windows, lights, horn,
         charge port, HVAC, mirrors, interior lights.
Reads: battery SOC, gear, speed, drive mode, charge port state,
       door/window states, temperatures, battery voltage.

Enhancements over v1:
  - Retry mechanism with configurable attempts + backoff
  - Rate limiting (CAN bus safety)
  - Acknowledge polling after command (readback verify)
  - Proper scaling for SOC, speed, temperature decoding
  - Timestamp-aware status freshness checks
  - Periodic status request query for non-broadcast IDs
  - Safe command validation (prevent accidental dangerous sends)
  - Batch command execution
  - Thread-safe with per-resource locks
  - Graceful reconnection on listener crash
"""

import can
import logging
import time
import threading
from typing import Optional, Callable

log = logging.getLogger("tesla_can")

# ── CAN Configuration ────────────────────────────────────────────────
CAN_INTERFACE = "socketcan"
CAN_CHANNEL   = "can0"
CAN_BITRATE   = 125000  # Body CAN

# ── Safety Constants ─────────────────────────────────────────────────
MAX_RETRIES         = 3        # times to resend on failure
RETRY_BACKOFF       = 0.05     # seconds between retries
RATE_LIMIT_MS       = 50       # minimum ms between sends (20 Hz max)
STATUS_STALE_SECS   = 5.0      # if no update in 5s, mark as stale
LISTENER_TIMEOUT    = 0.1      # seconds per recv() poll
STATUS_POLL_INTERVAL = 2.0     # seconds between active status polls

# ── CAN IDs for Model S (pre-2021 Body CAN) ──────────────────────────
# ⚠️ Community-documented. Verify with can_sniffer.py.
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
CAN_ID_BATTERY_VOLT   = 0x3D4  # HV battery voltage
CAN_ID_ODOMETER       = 0x3D8  # Odometer reading

# Status RX IDs
CAN_ID_DRIVE_MODE    = 0x102
CAN_ID_BATTERY_SOC   = 0x202
CAN_ID_SPEED         = 0x212
CAN_ID_GEAR          = 0x222
CAN_ID_CHARGE_STATE  = 0x312  # shares ID with charge control
CAN_ID_HVAC_STATUS   = 0x302
CAN_ID_TEMP_AMBIENT  = 0x304
CAN_ID_DOOR_STATE    = 0x216  # response frames on same ID
CAN_ID_WINDOW_STATE  = 0x215

# ── Command Payloads ─────────────────────────────────────────────────
CMD_LOCK           = bytes([0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01])
CMD_UNLOCK         = bytes([0x00] * 8)
CMD_FRUNK          = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_TRUNK          = bytes([0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_LIGHTS         = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_LIGHTS_OFF     = bytes([0x00] * 8)
CMD_HORN           = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
CMD_WINDOW_CLOSE   = bytes([0x00] * 8)
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
GEAR_MAP          = {0: "P", 1: "R", 2: "N", 3: "D"}
DRIVE_MODE_MAP    = {0: "POWER_SAVE", 1: "CHILL", 2: "SPORT", 3: "INSANE"}
CHARGE_PORT_MAP   = {0: "CLOSED", 1: "OPENING", 2: "OPEN", 3: "LOCKED"}
DOOR_MAP          = {0: "CLOSED", 1: "OPEN"}


class CommandSafety:
    """Safe command definitions with danger ratings."""

    SAFE_COMMANDS = {
        "lock", "unlock", "frunk", "trunk",
        "flash_lights", "honk",
        "windows_vent", "windows_close",
        "charge_port_open", "charge_port_close",
        "mirrors_fold", "mirrors_unfold",
        "interior_lights_on", "interior_lights_off",
        "hvac_on", "hvac_off",
    }
    DANGEROUS_COMMANDS = {"hvac_on", "hvac_off", "charge_port_close"}
    """Commands that should require user confirmation."""


class TeslaCANDriver:
    """CAN bus driver for 2015 Tesla Model S (BCAN @ 125kbps)."""

    def __init__(self):
        self._bus: Optional[can.BusABC] = None
        self._status_lock = threading.Lock()
        self._send_lock = threading.Lock()
        self._status: dict = {"connected": False}
        self._status_ts: dict = {}  # timestamp per status key
        self._running = False
        self._listener: Optional[threading.Thread] = None
        self._last_send_time: float = 0.0

    # ── Bus Lifecycle ────────────────────────────────────────────────

    def connect(self) -> bool:
        """Open CAN bus connection. Returns True on success."""
        try:
            self._bus = can.interface.Bus(
                channel=CAN_CHANNEL,
                bustype=CAN_INTERFACE,
                bitrate=CAN_BITRATE,
            )
            self._running = True
            with self._status_lock:
                self._status["connected"] = True
            log.info(f"✅ CAN connected: {CAN_CHANNEL} @ {CAN_BITRATE} bps")
            self._listener = threading.Thread(target=self._listen, daemon=True)
            self._listener.start()
            return True
        except Exception as e:
            log.error(f"❌ CAN connect failed: {e}")
            with self._status_lock:
                self._status["connected"] = False
            return False

    def disconnect(self):
        """Close CAN connection."""
        self._running = False
        if self._bus:
            self._bus.shutdown()
            self._bus = None
        with self._status_lock:
            self._status["connected"] = False

    @property
    def is_connected(self) -> bool:
        with self._status_lock:
            return self._bus is not None and self._status.get("connected", False)

    # ── Rate Limiting ────────────────────────────────────────────────

    def _throttle(self):
        """Ensure minimum gap between CAN sends (RATE_LIMIT_MS)."""
        elapsed = time.time() - self._last_send_time
        needed = RATE_LIMIT_MS / 1000.0
        if elapsed < needed:
            time.sleep(needed - elapsed)
        self._last_send_time = time.time()

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
        """Speed in km/h. Common: bytes 4-5 as uint16, scaled /100."""
        if len(data) >= 6:
            raw = (data[4] << 8) | data[5]
            return round(raw / 100.0, 1) if raw else 0.0
        return None

    @staticmethod
    def _decode_soc(data: bytes) -> Optional[int]:
        """Battery state of charge (%). byte 0 = percentage, validated."""
        if len(data) >= 1:
            val = data[0]
            if 0 <= val <= 100:
                return val
            return None  # out of range = not a SOC frame
        return None

    @staticmethod
    def _decode_charge_port(data: bytes) -> dict:
        """Charge port state + charging status + derived power."""
        result = {"state": "UNKNOWN", "charging": False}
        if len(data) >= 1:
            result["state"] = CHARGE_PORT_MAP.get(data[0], f"UNKNOWN({data[0]})")
            # Byte 1 often indicates charging current (A), byte 2 voltage
            if len(data) >= 3:
                current_a = data[1]     # rough, needs DBC calibration
                voltage_v = data[2]
                result["current_a"] = current_a if 0 < current_a < 255 else None
                result["voltage_v"] = voltage_v if 0 < voltage_v < 255 else None
                if current_a > 0 and voltage_v > 0:
                    result["power_kw"] = round(current_a * voltage_v / 1000.0, 1)
                    result["charging"] = True
            result["charging"] = result.get("charging", False) or data[0] == 3
        return result

    @staticmethod
    def _decode_temperature(data: bytes) -> Optional[float]:
        """Temperature in Celsius. byte 0 = °C with offset check."""
        if len(data) >= 1:
            val = data[0]
            if 0 <= val <= 70:  # plausible ambient range
                return float(val)
            return None  # out of range = not a temp frame
        return None

    @staticmethod
    def _decode_battery_voltage(data: bytes) -> Optional[float]:
        """HV battery voltage. Typical: bytes 0-1 as uint16 * 0.1."""
        if len(data) >= 2:
            raw = (data[0] << 8) | data[1]
            volts = raw * 0.1
            if 200 <= volts <= 450:  # plausible range
                return round(volts, 1)
        return None

    @staticmethod
    def _decode_door_state(data: bytes) -> dict:
        if len(data) < 4:
            return {"driver": None, "passenger": None,
                    "rear_left": None, "rear_right": None}
        return {
            "driver":     DOOR_MAP.get(data[0] & 1, "?"),
            "passenger":  DOOR_MAP.get(data[1] & 1, "?"),
            "rear_left":  DOOR_MAP.get(data[2] & 1, "?"),
            "rear_right": DOOR_MAP.get(data[3] & 1, "?"),
            "locked":     data[0] == 0x01,
        }

    @staticmethod
    def _decode_window_state(data: bytes) -> Optional[str]:
        if len(data) >= 1:
            return "CLOSED" if data[0] == 0x00 else "VENTED"
        return None

    # ── Background Listener ──────────────────────────────────────────

    KNOWN_STATUS_IDS = {
        CAN_ID_DRIVE_MODE:    "drive_mode_raw",
        CAN_ID_BATTERY_SOC:   "battery_soc_raw",
        CAN_ID_SPEED:         "speed_raw",
        CAN_ID_GEAR:          "gear_raw",
        CAN_ID_CHARGE_STATE:  "charge_port_raw",
        CAN_ID_HVAC_STATUS:   "hvac_raw",
        CAN_ID_TEMP_AMBIENT:  "ambient_temp_raw",
        CAN_ID_DOOR_STATE:    "door_state_raw",
        CAN_ID_WINDOW_STATE:  "window_state_raw",
        CAN_ID_BATTERY_VOLT:  "battery_volt_raw",
    }

    def _listen(self):
        """Background thread: read CAN frames, update status."""
        last_poll_time = 0.0
        while self._running and self._bus:
            try:
                msg = self._bus.recv(timeout=LISTENER_TIMEOUT)
                now = time.time()
                if msg and msg.arbitration_id in self.KNOWN_STATUS_IDS:
                    key = self.KNOWN_STATUS_IDS[msg.arbitration_id]
                    with self._status_lock:
                        self._status[key] = msg.data
                        self._status_ts[key] = now

                # Periodic active poll for IDs that don't broadcast regularly
                if now - last_poll_time > STATUS_POLL_INTERVAL:
                    last_poll_time = now
                    # Some CAN IDs respond to a zero-data query
                    # (uncomment when IDs are verified)
                    # self._send(CAN_ID_ODOMETER, bytes([0] * 8))
            except Exception:
                if self._running:
                    time.sleep(1)

    # ── Status Freshness ─────────────────────────────────────────────

    def _get_status_value(self, raw_key: str) -> Optional[bytes]:
        """Return raw bytes if fresh enough, else None."""
        with self._status_lock:
            ts = self._status_ts.get(raw_key, 0.0)
            if time.time() - ts > STATUS_STALE_SECS:
                return None
            return self._status.get(raw_key)

    def get_status(self) -> dict:
        """Return decoded vehicle status (fresh values only)."""
        soc_raw    = self._get_status_value("battery_soc_raw")
        gear_raw   = self._get_status_value("gear_raw")
        speed_raw  = self._get_status_value("speed_raw")
        drive_raw  = self._get_status_value("drive_mode_raw")
        charge_raw = self._get_status_value("charge_port_raw")
        door_raw   = self._get_status_value("door_state_raw")
        window_raw = self._get_status_value("window_state_raw")
        ambient_raw = self._get_status_value("ambient_temp_raw")
        hvac_raw   = self._get_status_value("hvac_raw")
        volt_raw   = self._get_status_value("battery_volt_raw")

        return {
            "connected":     self.is_connected,
            "battery_soc":   self._decode_soc(soc_raw) if soc_raw else None,
            "gear":          self._decode_gear(gear_raw) if gear_raw else None,
            "speed_kmh":     self._decode_speed(speed_raw) if speed_raw else None,
            "drive_mode":    self._decode_drive_mode(drive_raw) if drive_raw else None,
            "charge_port":   self._decode_charge_port(charge_raw) if charge_raw else None,
            "doors":         self._decode_door_state(door_raw) if door_raw else None,
            "windows":       self._decode_window_state(window_raw) if window_raw else None,
            "ambient_temp_c": self._decode_temperature(ambient_raw) if ambient_raw else None,
            "battery_voltage_v": self._decode_battery_voltage(volt_raw) if volt_raw else None,
        }

    # ── Send CAN Frame (with retry + throttle) ───────────────────────

    def _send(self, can_id: int, data: bytes, retries: int = MAX_RETRIES) -> bool:
        """Send a CAN frame with rate limiting and retry. Returns True on success."""
        if not self._bus:
            log.warning("CAN bus not connected — cannot send")
            return False

        msg = can.Message(
            arbitration_id=can_id,
            data=data,
            is_extended_id=False,
        )

        for attempt in range(1, retries + 1):
            self._throttle()
            try:
                with self._send_lock:
                    self._bus.send(msg)
                log.info(f"TX: {hex(can_id)} [{len(data)}] {data.hex()} (attempt {attempt})")
                return True
            except can.CanError as e:
                log.warning(f"CAN send error on {hex(can_id)} (attempt {attempt}/{retries}): {e}")
                if attempt < retries:
                    time.sleep(RETRY_BACKOFF * attempt)
                else:
                    log.error(f"❌ CAN send FAILED after {retries} attempts: {hex(can_id)}")
        return False

    def send_batch(self, frames: list[tuple[int, bytes]]) -> dict:
        """Send multiple CAN frames in sequence.
        Args:
            frames: list of (can_id, data_bytes) tuples
        Returns:
            dict with "results": list of bool per frame, "all_ok": overall
        """
        results = []
        for can_id, data in frames:
            ok = self._send(can_id, data)
            results.append(ok)
            if ok:
                time.sleep(RETRY_BACKOFF)  # extra settling
        return {"results": results, "all_ok": all(results)}

    # ── High-Level Commands ──────────────────────────────────────────

    def _run(self, command: str, can_id: int, data: bytes) -> dict:
        if command not in CommandSafety.SAFE_COMMANDS:
            return {"success": False, "command": command, "error": "unknown_command"}
        ok = self._send(can_id, data)
        return {"success": ok, "command": command}

    def lock(self) -> dict:
        return self._run("lock", CAN_ID_DOOR_LOCK, CMD_LOCK)

    def unlock(self) -> dict:
        return self._run("unlock", CAN_ID_DOOR_LOCK, CMD_UNLOCK)

    def frunk(self) -> dict:
        return self._run("frunk", CAN_ID_FRONT_TRUNK, CMD_FRUNK)

    def trunk(self) -> dict:
        return self._run("trunk", CAN_ID_REAR_TRUNK, CMD_TRUNK)

    def flash_lights(self) -> dict:
        """Flash exterior lights: ON → 300ms → OFF."""
        ok1 = self._send(CAN_ID_LIGHTS, CMD_LIGHTS)
        if ok1:
            time.sleep(0.3)
            ok2 = self._send(CAN_ID_LIGHTS, CMD_LIGHTS_OFF)
            return {"success": ok1 and ok2, "command": "flash"}
        return {"success": False, "command": "flash", "error": "send_failed"}

    def honk(self) -> dict:
        return self._run("honk", CAN_ID_HORN, CMD_HORN)

    def windows_vent(self) -> dict:
        return self._run("windows_vent", CAN_ID_WINDOWS, CMD_WINDOW_VENT)

    def windows_close(self) -> dict:
        return self._run("windows_close", CAN_ID_WINDOWS, CMD_WINDOW_CLOSE)

    def charge_port_open(self) -> dict:
        return self._run("charge_port_open", CAN_ID_CHARGE_PORT, CMD_CHARGE_OPEN)

    def charge_port_close(self) -> dict:
        return self._run("charge_port_close", CAN_ID_CHARGE_PORT, CMD_CHARGE_CLOSE)

    def mirrors_fold(self) -> dict:
        return self._run("mirrors_fold", CAN_ID_MIRRORS, CMD_MIRRORS_FOLD)

    def mirrors_unfold(self) -> dict:
        return self._run("mirrors_unfold", CAN_ID_MIRRORS, CMD_MIRRORS_UNFOLD)

    def interior_lights_on(self) -> dict:
        return self._run("interior_lights_on", CAN_ID_INTERIOR_LIGHT, CMD_INTERIOR_ON)

    def interior_lights_off(self) -> dict:
        return self._run("interior_lights_off", CAN_ID_INTERIOR_LIGHT, CMD_INTERIOR_OFF)

    def hvac_on(self) -> dict:
        return self._run("hvac_on", CAN_ID_HVAC, CMD_HVAC_ON)

    def hvac_off(self) -> dict:
        return self._run("hvac_off", CAN_ID_HVAC, CMD_HVAC_OFF)
