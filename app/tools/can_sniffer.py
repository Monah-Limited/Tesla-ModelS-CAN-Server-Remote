#!/usr/bin/env python3
"""
CAN Sniffer — Tesla Model S Body CAN
=====================================
Run this on the Orange Pi with CAN hat connected to the car.
Sniffs all CAN IDs so you can find the right ones for lock/unlock etc.

Usage:
  1. Connect MCP2515 → OBD pins 1(BCAN_H), 9(BCAN_L), 4(GND)
  2. Turn car ON (Accessory mode)
  3. Run: python3 can_sniffer.py
  4. Press each button (lock, unlock, frunk, etc.)
  5. Note which CAN ID changes → update tesla_can.py
"""

import can
import time
import json
import signal
from collections import defaultdict
from datetime import datetime

BUS = "can0"
BITRATE = 125000
DURATION = 90  # seconds

counts = defaultdict(int)
data_samples = {}
running = True

def handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, handler)

def main():
    global running
    print("=" * 60)
    print("🚗 Tesla Model S CAN Sniffer")
    print("=" * 60)
    print(f"Interface: {BUS} @ {BITRATE} bps")
    print(f"Duration:  {DURATION}s")
    print()
    print("Instructions:")
    print("  1. Car ON (Accessory mode)")
    print("  2. Sniffing starts NOW — press each button once:")
    print("     🔒 Lock     🔓 Unlock")
    print("     🟢 Frunk    🟤 Trunk")
    print("     Wait a few seconds between each press")
    print()
    print("Starting in 3s...")
    time.sleep(3)

    try:
        bus = can.Bus(channel=BUS, bustype="socketcan", bitrate=BITRATE)
    except Exception as e:
        print(f"❌ CAN init failed: {e}")
        print("   Try: sudo ip link set can0 up type can bitrate 125000")
        return

    start = time.time()
    print(f"\n📡 Sniffing... ({DURATION}s remaining)")
    print("-" * 60)

    while running and (time.time() - start) < DURATION:
        msg = bus.recv(timeout=0.1)
        if msg:
            cid = msg.arbitration_id
            counts[cid] += 1
            if cid not in data_samples:
                data_samples[cid] = {
                    "data": msg.data.hex(),
                    "dlc": msg.dlc,
                    "first": datetime.now().isoformat(),
                }
            data_samples[cid]["last"] = datetime.now().isoformat()
            data_samples[cid]["count"] = counts[cid]

    # Results
    print("\n" + "=" * 60)
    print("📊 Results — Most Active CAN IDs")
    print("=" * 60)
    print(f"{'CAN ID':<10} {'Count':<8} {'Data':<24}  Notes")
    print("-" * 60)

    # Known Model S Body CAN IDs for reference
    known = {
        0x216: "DOOR LOCK",
        0x215: "WINDOWS",
        0x217: "FRUNK",
        0x218: "TRUNK",
        0x244: "LIGHTS",
        0x245: "HORN",
        0x312: "CHARGE PORT",
    }

    for cid in sorted(counts, key=counts.get, reverse=True)[:30]:
        info = data_samples[cid]
        note = known.get(cid, "")
        star = "⭐ " if note else "  "
        print(f"0x{cid:03X}    {info['count']:<8} {info['data']:<24} {star}{note}")

    # Save
    output = {
        "captured": datetime.now().isoformat(),
        "total_ids": len(counts),
        "messages": {f"0x{k:03X}": v for k, v in sorted(data_samples.items())},
    }
    with open("/opt/tesla-control/can_sniff_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 Saved: can_sniff_results.json")
    print(f"\n👉 Edit /opt/tesla-control/app/tesla_can.py and update CAN IDs")

if __name__ == "__main__":
    main()
