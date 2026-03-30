import re
import logging

logger = logging.getLogger(__name__)

# Home Depot store number patterns
STORE_NUMBER_PATTERNS = [
    re.compile(r"(?:store|location)\s*#?\s*(\d{4})", re.IGNORECASE),
    re.compile(r"#(\d{4})\b"),
    re.compile(r"HD\s*(\d{4})\b", re.IGNORECASE),
]

# California ZIP codes (start with 9)
ZIP_PATTERN = re.compile(r"\b(9[0-9]{4})\b")

# Known Bay Area Home Depot stores
BAY_AREA_STORES = {
    "0601": {"name": "Colma", "address": "150 Colma Blvd, Colma, CA 94014"},
    "0611": {"name": "San Francisco", "address": "2 Bayshore Blvd, San Francisco, CA 94124"},
    "1009": {"name": "Emeryville", "address": "3838 Hollis St, Emeryville, CA 94608"},
    "1011": {"name": "Dublin", "address": "6000 Dublin Blvd, Dublin, CA 94568"},
    "1012": {"name": "San Jose - Almaden", "address": "635 W Capitol Expy, San Jose, CA 95136"},
    "1019": {"name": "Concord", "address": "1975 Diamond Blvd, Concord, CA 94520"},
    "1021": {"name": "Sunnyvale", "address": "811 E Arques Ave, Sunnyvale, CA 94085"},
    "1025": {"name": "San Jose - Story", "address": "2181 Monterey Rd, San Jose, CA 95112"},
    "1038": {"name": "Fremont", "address": "39100 Argonaut Way, Fremont, CA 94538"},
    "1040": {"name": "Mountain View", "address": "2450 Charleston Rd, Mountain View, CA 94043"},
    "1044": {"name": "Oakland", "address": "4000 Alameda Ave, Oakland, CA 94601"},
    "1049": {"name": "Hayward", "address": "25700 Clawiter Rd, Hayward, CA 94545"},
    "1050": {"name": "San Mateo", "address": "2001 Bridgepointe Pkwy, San Mateo, CA 94404"},
    "1053": {"name": "Richmond", "address": "5401 Central Ave, Richmond, CA 94804"},
    "1056": {"name": "Walnut Creek", "address": "2000 N Main St, Walnut Creek, CA 94596"},
    "1060": {"name": "Milpitas", "address": "301 Ranch Dr, Milpitas, CA 95035"},
    "1062": {"name": "Redwood City", "address": "2303 Broadway, Redwood City, CA 94063"},
    "1067": {"name": "Gilroy", "address": "6975 Camino Arroyo, Gilroy, CA 95020"},
    "1082": {"name": "Livermore", "address": "4255 First St, Livermore, CA 94551"},
}

# Bay Area ZIP code ranges (approximate)
BAY_AREA_ZIPS = set()
for prefix in range(940, 960):
    for suffix in range(100):
        BAY_AREA_ZIPS.add(str(prefix * 100 + suffix).zfill(5))


def extract_store_info(text: str) -> dict:
    """Extract store number, ZIP code, and generate Maps link."""
    result = {
        "store_number": None,
        "store_name": None,
        "zip_code": None,
        "is_bay_area": False,
        "maps_url": None,
    }

    # Find store number
    for pattern in STORE_NUMBER_PATTERNS:
        match = pattern.search(text)
        if match:
            store_num = match.group(1)
            result["store_number"] = store_num
            if store_num in BAY_AREA_STORES:
                store = BAY_AREA_STORES[store_num]
                result["store_name"] = store["name"]
                result["is_bay_area"] = True
                address = store["address"].replace(" ", "+")
                result["maps_url"] = f"https://www.google.com/maps/search/?api=1&query={address}"
            break

    # Find ZIP code
    for match in ZIP_PATTERN.finditer(text):
        zip_code = match.group(1)
        result["zip_code"] = zip_code
        if zip_code in BAY_AREA_ZIPS:
            result["is_bay_area"] = True
            if not result["maps_url"]:
                result["maps_url"] = f"https://www.google.com/maps/search/Home+Depot+{zip_code}"
        break

    return result
