"""
Tesla Model Database — All models, years, colors, VIN decoder
==============================================================
"""
# ── All Tesla Models Ever Made ───────────────────────────────────────

TESLA_MODELS = [
    # ── Roadster ──
    {"id": "roadster_10", "name": "Roadster 1.0", "years": "2008-2012",
     "brand": "Tesla", "type": "Sports", "body": "Convertible",
     "vin_prefix": ["5YJRE1"], "battery": "53kWh", "range_km": 393},

    # ── Model S ──
    {"id": "ms_40",    "name": "Model S 40",       "years": "2013",        "vin_prefix": ["5YJSA1", "5YJSA2"], "battery": "40kWh", "range_km": 260},
    {"id": "ms_60",    "name": "Model S 60",       "years": "2013-2016",   "vin_prefix": ["5YJSA1", "5YJSA3"], "battery": "60kWh", "range_km": 335},
    {"id": "ms_60d",   "name": "Model S 60D",      "years": "2014-2016",   "vin_prefix": ["5YJSA7"],          "battery": "60kWh", "range_km": 351},  # dual motor
    {"id": "ms_85",    "name": "Model S 85",       "years": "2013-2015",   "vin_prefix": ["5YJSA4"],          "battery": "85kWh", "range_km": 426},
    {"id": "ms_85d",   "name": "Model S 85D",      "years": "2014-2016",   "vin_prefix": ["5YJSA7", "5YJSB7"], "battery": "85kWh", "range_km": 443},  # ⭐你的车
    {"id": "ms_p85",   "name": "Model S P85",      "years": "2013-2015",   "vin_prefix": ["5YJSA5"],          "battery": "85kWh", "range_km": 426},
    {"id": "ms_p85d",  "name": "Model S P85D",     "years": "2014-2016",   "vin_prefix": ["5YJSA7"],          "battery": "85kWh", "range_km": 436},
    {"id": "ms_90",    "name": "Model S 90",       "years": "2015-2016",   "vin_prefix": ["5YJSA8"],          "battery": "90kWh", "range_km": 473},
    {"id": "ms_90d",   "name": "Model S 90D",      "years": "2015-2017",   "vin_prefix": ["5YJSA7"],          "battery": "90kWh", "range_km": 473},
    {"id": "ms_p90d",  "name": "Model S P90D",     "years": "2015-2017",   "vin_prefix": ["5YJSA7"],          "battery": "90kWh", "range_km": 435},
    {"id": "ms_100d",  "name": "Model S 100D",     "years": "2017-2020",   "vin_prefix": ["5YJSA7"],          "battery": "100kWh","range_km": 539},
    {"id": "ms_p100d", "name": "Model S P100D",    "years": "2017-2019",   "vin_prefix": ["5YJSA7"],          "battery": "100kWh","range_km": 507},
    {"id": "ms_lr",    "name": "Model S Long Range","years": "2019-2024",  "vin_prefix": ["5YJSA7", "LRW"],    "battery": "100kWh","range_km": 652},
    {"id": "ms_plaid", "name": "Model S Plaid",    "years": "2021-2025",   "vin_prefix": ["5YJSA7", "LRW"],    "battery": "100kWh","range_km": 628},
    {"id": "ms_plaid_plus","name": "Model S Plaid+","years": "2022-2025",  "vin_prefix": ["5YJSA7"],          "battery": "100kWh","range_km": 658},
    {"id": "ms_standard","name": "Model S Standard Range","years":"2024-", "vin_prefix": ["5YJSA7", "LRW"],   "battery": "75kWh", "range_km": 450},

    # ── Model X ──
    {"id": "mx_75d",   "name": "Model X 75D",     "years": "2016-2018",   "vin_prefix": ["5YJXCA4", "5YJXC"], "battery": "75kWh", "range_km": 381},
    {"id": "mx_90d",   "name": "Model X 90D",     "years": "2015-2016",   "vin_prefix": ["5YJXCA4", "5YJXC"], "battery": "90kWh", "range_km": 414},
    {"id": "mx_p90d",  "name": "Model X P90D",    "years": "2015-2016",   "vin_prefix": ["5YJXCA4", "5YJXC"], "battery": "90kWh", "range_km": 402},
    {"id": "mx_100d",  "name": "Model X 100D",    "years": "2017-2020",   "vin_prefix": ["5YJXCA4", "5YJXC"], "battery": "100kWh","range_km": 565},
    {"id": "mx_p100d", "name": "Model X P100D",   "years": "2016-2019",   "vin_prefix": ["5YJXCA4", "5YJXC"], "battery": "100kWh","range_km": 542},
    {"id": "mx_lr",    "name": "Model X Long Range","years":"2019-2024",  "vin_prefix": ["5YJXCA4", "LRW"],    "battery": "100kWh","range_km": 580},
    {"id": "mx_plaid", "name": "Model X Plaid",   "years": "2021-2025",   "vin_prefix": ["5YJXCA4", "LRW"],    "battery": "100kWh","range_km": 536},
    {"id": "mx_standard","name": "Model X Standard Range","years":"2024-","vin_prefix": ["5YJXCA4", "LRW"],    "battery": "75kWh", "range_km": 400},

    # ── Model 3 ──
    {"id": "m3_sr",    "name": "Model 3 Standard Range","years":"2017-2021","vin_prefix":["5YJ3LA","LRW3"],   "battery":"50kWh","range_km": 354},
    {"id": "m3_srp",   "name": "Model 3 Standard Range Plus","years":"2019-2023","vin_prefix":["5YJ3LA","LRW3"],"battery":"54kWh","range_km": 423},
    {"id": "m3_sr_plus","name":"Model 3 SR+ (China)","years":"2021-2023","vin_prefix":["LRW3"],              "battery":"55kWh","range_km": 448},
    {"id": "m3_mr",    "name": "Model 3 Mid Range","years":"2018-2019",   "vin_prefix":["5YJ3LA"],           "battery":"62kWh","range_km": 418},
    {"id": "m3_lr_rwd","name": "Model 3 Long Range RWD","years":"2017-2019","vin_prefix":["5YJ3LA"],         "battery":"75kWh","range_km": 499},
    {"id": "m3_lr_awd","name": "Model 3 Long Range AWD","years":"2018-2024","vin_prefix":["5YJ3LE","LRW3"],  "battery":"75-82kWh","range_km": 568},
    {"id": "m3_perf",  "name": "Model 3 Performance","years":"2018-2024",  "vin_prefix":["5YJ3LE","LRW3"],    "battery":"75-82kWh","range_km": 507},

    # ── Model Y ──
    {"id": "my_rwd",   "name": "Model Y RWD",     "years": "2021-2024",   "vin_prefix":["5YJY","LRWY"],      "battery":"60-75kWh","range_km": 455},
    {"id": "my_lr_awd","name":"Model Y Long Range AWD","years":"2020-2025","vin_prefix":["5YJY","LRWY"],      "battery":"75-82kWh","range_km": 533},
    {"id": "my_perf",  "name":"Model Y Performance","years":"2020-2025",  "vin_prefix":["5YJY","LRWY"],      "battery":"75-82kWh","range_km": 488},

    # ── Cybertruck ──
    {"id": "ct_beast", "name":"Cybertruck Cyberbeast","years":"2024-",    "vin_prefix":["7G2"],               "battery":"123kWh","range_km": 515},
    {"id": "ct_awd",   "name":"Cybertruck AWD",   "years": "2024-",       "vin_prefix":["7G2"],               "battery":"123kWh","range_km": 547},
    {"id": "ct_rwd",   "name":"Cybertruck RWD",   "years": "2025-",       "vin_prefix":["7G2"],               "battery":"123kWh","range_km": 400},

    # ── Semi ──
    {"id": "semi",     "name":"Tesla Semi",       "years": "2022-",       "vin_prefix":["7G2"],               "battery":"900kWh","range_km": 800},
]


# ── Tesla Paint Colors ───────────────────────────────────────────────

TESLA_COLORS = [
    {"id": "pearl_white",      "name_cn": "珍珠白",      "name_en": "Pearl White Multi-Coat",   "hex": "#f5f5f0"},
    {"id": "solid_black",      "name_cn": "纯黑",        "name_en": "Solid Black",             "hex": "#1a1a1a"},
    {"id": "obsidian_black",   "name_cn": "曜石黑",      "name_en": "Obsidian Black",          "hex": "#282828"},
    {"id": "midnight_silver",  "name_cn": "午夜银",      "name_en": "Midnight Silver Metallic", "hex": "#6b6b6b"},
    {"id": "deep_blue",        "name_cn": "深海蓝",      "name_en": "Deep Blue Metallic",       "hex": "#1a2b5c"},
    {"id": "solid_blue",       "name_cn": "纯蓝",        "name_en": "Blue Metallic",            "hex": "#2b5c8a"},
    {"id": "red_multicoat",    "name_cn": "中国红",      "name_en": "Red Multi-Coat",           "hex": "#c41e2a"},
    {"id": "signature_red",    "name_cn": "签名红",      "name_en": "Signature Red",            "hex": "#b81a24"},
    {"id": "silver",           "name_cn": "银色",        "name_en": "Silver Metallic",          "hex": "#c0c0c0"},
    {"id": "titanium",         "name_cn": "钛银色",      "name_en": "Titanium Metallic",        "hex": "#9a9a9a"},
    {"id": "brown",            "name_cn": "棕色",        "name_en": "Brown",                    "hex": "#5a3a2a"},
    {"id": "green",            "name_cn": "绿色",        "name_en": "Green Metallic",           "hex": "#2a5a3a"},
    {"id": "stealth_grey",     "name_cn": "隐形灰",      "name_en": "Stealth Grey",             "hex": "#4a4a52"},
    {"id": "ultra_red",        "name_cn": "超红",        "name_en": "Ultra Red",                "hex": "#d42e3a"},
    {"id": "quicksilver",      "name_cn": "水银银",      "name_en": "Quicksilver",              "hex": "#b8b8bc"},
]


# ── VIN Decoder ──────────────────────────────────────────────────────

# WMI (World Manufacturer Identifier)
WMI = {
    "5YJ":  {"brand": "Tesla", "country": "USA",     "plant": "Fremont, CA"},
    "LRW":  {"brand": "Tesla", "country": "China",   "plant": "Shanghai"},
    "SFZ":  {"brand": "Tesla", "country": "Netherlands","plant": "Tilburg"},
    "XP7":  {"brand": "Tesla", "country": "Germany", "plant": "Berlin-Brandenburg"},
    "7G2":  {"brand": "Tesla", "country": "USA",     "plant": "Texas Giga"},
}

# Model year from VIN digit 10
MODEL_YEARS = {
    "A": 2010, "B": 2011, "C": 2012, "D": 2013, "E": 2014,
    "F": 2015, "G": 2016, "H": 2017, "J": 2018, "K": 2019,
    "L": 2020, "M": 2021, "N": 2022, "P": 2023, "R": 2024,
    "S": 2025, "T": 2026,
}


def decode_vin(vin: str) -> dict:
    """
    Decode a Tesla VIN and return vehicle info.
    
    VIN structure for Tesla (17 characters):
      1-3  WMI (World Manufacturer Identifier)
      4    Restraint system / Body type
      5    Brand / Market
      6-7  Model line
      8    Motor / Drivetrain
      9    Check digit
      10   Model year
      11   Plant
      12-17 Serial number

    Returns dict with matched model, year, plant, or error.
    """
    vin = vin.upper().strip()
    
    if len(vin) != 17:
        return {"error": "VIN 必须是 17 位字符"}
    
    # Validate characters (no I, O, Q)
    for c in "IOQ":
        if c in vin:
            return {"error": f"VIN 不能包含字母 {c}"}
    
    result = {"vin": vin}
    
    # WMI
    wmi_code = vin[:3]
    if wmi_code in WMI:
        result["origin"] = WMI[wmi_code]
    else:
        result["origin"] = {"brand": "Tesla (other)", "country": "?", "plant": "?"}
    
    # Model year
    year_char = vin[9]
    if year_char in MODEL_YEARS:
        result["year"] = MODEL_YEARS[year_char]
    else:
        result["year"] = None
    
    # Plant code
    plant_char = vin[10]
    plant_map = {
        "C": "Fremont, CA", "P": "Fremont/Palo Alto",
        "F": "Fremont", "A": "Austin, TX",
        "G": "Berlin, Germany", "H": "Shanghai, China",
    }
    result["plant_code"] = plant_char
    result["plant"] = plant_map.get(plant_char, f"Unknown ({plant_char})")
    
    # Find matching model from database
    matched = []
    for m in TESLA_MODELS:
        for prefix in m["vin_prefix"]:
            if vin.startswith(prefix):
                matched.append(m)
                break
    
    if matched:
        # Pick the most specific match (longest prefix)
        def prefix_len(model):
            for p in model["vin_prefix"]:
                if vin.startswith(p):
                    return len(p)
            return 0
        best = max(matched, key=prefix_len)
        result["model"] = best
        result["model_found"] = True
    else:
        # Try broader match by body type from digit 4
        body_type = vin[3]
        body_map = {
            "S": "Model S", "R": "Roadster",
            "X": "Model X", "3": "Model 3",
            "Y": "Model Y", "C": "Cybertruck",
        }
        body = body_map.get(body_type)
        if body:
            result["model"] = {"name": body, "note": "VIN prefix not in database, guessed by body code"}
            result["model_found"] = True
        else:
            result["model"] = {"name": f"Unknown Tesla (body code: {body_type})"}
            result["model_found"] = False
    
    return result


# ── Helpers ──────────────────────────────────────────────────────────

def get_model_by_id(model_id: str):
    """Find a model by its ID."""
    for m in TESLA_MODELS:
        if m["id"] == model_id:
            return m
    return None


def get_models_by_body(body_type: str):
    """Get all models of a certain body type/era."""
    body_map = {
        "S": "Model S", "3": "Model 3",
        "X": "Model X", "Y": "Model Y",
        "R": "Roadster", "C": "Cybertruck",
    }
    name = body_map.get(body_type, "")
    return [m for m in TESLA_MODELS if m["name"].startswith(name)] if name else []
