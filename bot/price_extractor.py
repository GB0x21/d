import re
import logging

logger = logging.getLogger(__name__)

# Patterns for penny/low prices
PRICE_PATTERNS = [
    # $0.01, $0.03, $.01
    re.compile(r"\$\s*0?\.0[0-9]\b"),
    # "ringing up as $X.XX"
    re.compile(r"ringing\s+up\s+(?:as|at)\s+\$(\d+\.?\d*)", re.IGNORECASE),
    # "$1.00" or "$12.99" general price
    re.compile(r"\$(\d{1,4}\.?\d{0,2})\b"),
]

# Textual penny indicators
PENNY_PHRASES = [
    "penny", "one cent", "1 cent", "1¢", "0.01",
    "price error", "pricing error", "price mistake",
    "ringing up as", "scanning at",
]

# Original price patterns (for discount calculation)
ORIGINAL_PRICE_PATTERN = re.compile(
    r"(?:was|originally|reg(?:ular)?|msrp|retail)\s*\$?(\d{1,5}\.?\d{0,2})",
    re.IGNORECASE,
)


def extract_prices(text: str) -> dict:
    """Extract deal price, original price, and discount info from text."""
    result = {
        "deal_price": None,
        "original_price": None,
        "discount_pct": None,
        "is_penny": False,
        "price_text": "",
    }

    text_lower = text.lower()

    # Check penny phrases
    for phrase in PENNY_PHRASES:
        if phrase in text_lower:
            result["is_penny"] = True
            break

    # Extract deal price (lowest price found)
    prices_found = []
    for pattern in PRICE_PATTERNS:
        for match in pattern.finditer(text):
            try:
                price_str = match.group(1) if match.lastindex else match.group(0)
                price_str = price_str.replace("$", "").strip()
                price = float(price_str)
                if 0 < price < 10000:
                    prices_found.append(price)
            except (ValueError, IndexError):
                continue

    if prices_found:
        result["deal_price"] = min(prices_found)
        if result["deal_price"] <= 0.10:
            result["is_penny"] = True
        result["price_text"] = f"${result['deal_price']:.2f}"

    # Extract original price
    orig_match = ORIGINAL_PRICE_PATTERN.search(text)
    if orig_match:
        try:
            result["original_price"] = float(orig_match.group(1))
        except ValueError:
            pass

    # Calculate discount
    if result["deal_price"] and result["original_price"] and result["original_price"] > 0:
        discount = (1 - result["deal_price"] / result["original_price"]) * 100
        if 0 < discount <= 100:
            result["discount_pct"] = round(discount, 1)

    return result
