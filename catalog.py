import re

PRODUCTS = [
    {"id": 1, "name": "Blue Embroidered Kurti", "color": "blue", "price": 899, "category": "kurti", "sizes": ["S", "M", "L", "XL"]},
    {"id": 2, "name": "Maroon Festival Dress", "color": "maroon", "price": 1299, "category": "dress", "sizes": ["M", "L", "XL"]},
    {"id": 3, "name": "Green Cotton Kurti", "color": "green", "price": 699, "category": "kurti", "sizes": ["S", "M", "L"]},
    {"id": 4, "name": "Yellow Celebration Dress", "color": "yellow", "price": 999, "category": "dress", "sizes": ["S", "M", "L"]},
    {"id": 5, "name": "Blue Cotton Shirt", "color": "blue", "price": 749, "category": "shirt", "sizes": ["M", "L", "XL"]},
    {"id": 6, "name": "Pink Party Kurti", "color": "pink", "price": 1099, "category": "kurti", "sizes": ["S", "M", "L"]},
]

COLOR_TERMS = {
    "blue": ["blue", "నీలం", "నీలి", "नीला", "नीली"],
    "green": ["green", "ఆకుపచ్చ", "हरा", "हरी"],
    "maroon": ["maroon", "మెరూన్", "मरून"],
    "yellow": ["yellow", "పసుపు", "पीला", "पीली"],
    "pink": ["pink", "గులాబీ", "गुलाबी"],
}
CATEGORY_TERMS = {
    "kurti": ["kurti", "kurta", "కుర్తీ", "కుర్తి", "कुर्ती", "कुर्ता"],
    "dress": ["dress", "గౌను", "డ్రెస్", "ड्रेस", "गाउन"],
    "shirt": ["shirt", "షర్ట్", "शर्ट"],
}

def search_products(query: str, max_price: int | None = None, color: str | None = None):
    """Deterministic sample-catalog search; no live stock or AI API."""
    q = str(query or "").casefold()
    inferred_color = color.casefold() if color else next((c for c, words in COLOR_TERMS.items() if any(w in q for w in words)), None)
    category = next((c for c, words in CATEGORY_TERMS.items() if any(w in q for w in words)), None)
    if max_price is None:
        # Only interpret a number as a budget when there is a budget indicator.
        match = re.search(r"(?:under|below|less than|within|upto|up to|budget|₹|rs\.?|రూపాయ|లోపు|तक|से कम|के अंदर)\D{0,12}(\d[\d,]*)", q)
        if match:
            max_price = int(match.group(1).replace(",", ""))
        else:
            match = re.search(r"(\d[\d,]*)\s*(?:రూపాయల లోపు|లోపు|के अंदर|से कम|तक)", q)
            if match: max_price = int(match.group(1).replace(",", ""))
    found = [p for p in PRODUCTS if (not inferred_color or p["color"] == inferred_color)
             and (not category or p["category"] == category)
             and (max_price is None or p["price"] <= max_price)]
    return found[:6], {"color": inferred_color, "category": category, "max_price": max_price}


def assistant_reply(query: str):
    found, filters = search_products(query)
    if found:
        summary = f"I found {len(found)} matching sample products. " + " ".join(f'{p["name"]} for ₹{p["price"]}.' for p in found[:3])
    else:
        summary = "No sample products match those filters. Try a different color or budget."
    return {"reply": summary, "products": found, "filters": filters, "disclosure": "Demo catalog. Not live Amazon inventory or Alexa+ integration."}
