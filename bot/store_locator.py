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

# Known Bay Area Home Depot stores (user's target stores)
BAY_AREA_STORES = {
    "0625": {"name": "San Leandro", "address": "1933 Davis St, San Leandro, CA 94577"},
    "0627": {"name": "Emeryville", "address": "3838 Hollis St, Emeryville, CA 94608"},
    "0631": {"name": "Vallejo", "address": "401 Columbus Pkwy, Vallejo, CA 94591"},
    "0633": {"name": "San Rafael", "address": "5800 Northgate Dr, San Rafael, CA 94903"},
    "0634": {"name": "Concord", "address": "1975 Diamond Blvd, Concord, CA 94520"},
    "0637": {"name": "Fairfield", "address": "4599 Central Way, Fairfield, CA 94534"},
    "0638": {"name": "Fremont", "address": "39100 Argonaut Way, Fremont, CA 94538"},
    "0639": {"name": "Dublin", "address": "6000 Dublin Blvd, Dublin, CA 94568"},
    "0644": {"name": "Pittsburg", "address": "4527 Century Blvd, Pittsburg, CA 94565"},
    "1007": {"name": "Oakland", "address": "4000 Alameda Ave, Oakland, CA 94601"},
    "1015": {"name": "El Cerrito", "address": "6000 Potrero Ave, El Cerrito, CA 94530"},
    "1017": {"name": "Hayward", "address": "25700 Clawiter Rd, Hayward, CA 94545"},
    "1044": {"name": "Hercules", "address": "340 Sycamore Ave, Hercules, CA 94547"},
    "1045": {"name": "Napa", "address": "205 Soscol Ave, Napa, CA 94559"},
    "1076": {"name": "Brentwood", "address": "2501 Sand Creek Rd, Brentwood, CA 94513"},
    "1380": {"name": "Martinez", "address": "920 Arnold Dr, Martinez, CA 94553"},
    "6604": {"name": "San Ramon", "address": "2250 Camino Ramon, San Ramon, CA 94583"},
    "6641": {"name": "Livermore", "address": "4255 First St, Livermore, CA 94551"},
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
