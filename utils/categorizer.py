"""
utils/categorizer.py

Rule-based (NO AI, NO ML, NO API) category suggestion for expense
descriptions. Purely deterministic keyword matching so behaviour is
100% explainable and testable.
"""

# Order matters: categories are checked top-to-bottom, first match wins.
CATEGORY_KEYWORDS = {
    "Food": [
        "swiggy", "zomato", "restaurant", "cafe", "pizza",
        "burger", "food", "canteen",
    ],
    "Transport": [
        "uber", "ola", "rapido", "metro", "bus",
        "fuel", "petrol", "diesel",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "mall", "clothes", "shopping",
    ],
    "Bills": [
        "electricity", "water", "internet", "wifi",
        "mobile", "recharge", "rent",
    ],
    "Entertainment": [
        "netflix", "spotify", "movie", "cinema", "game",
    ],
    "Healthcare": [
        "hospital", "pharmacy", "medicine", "doctor", "clinic",
    ],
    "Education": [
        "college", "course", "book", "udemy", "coursera",
    ],
    "Travel": [
        "flight", "hotel", "train", "trip", "booking",
    ],
    "Groceries": [
        "grocery", "supermarket", "vegetables", "milk",
    ],
}


def suggest_category(description: str) -> str:
    """
    Suggest a category for a transaction description using simple,
    deterministic, case-insensitive keyword matching.

    Args:
        description: free-text transaction description.

    Returns:
        One of the keys in CATEGORY_KEYWORDS, or "Other" if nothing
        matches (or the description is empty/invalid).

    Examples:
        >>> suggest_category("Swiggy dinner")
        'Food'
        >>> suggest_category("Uber to college")
        'Transport'
        >>> suggest_category("Amazon headphones")
        'Shopping'
        >>> suggest_category("random payment")
        'Other'
    """
    if not description or not isinstance(description, str):
        return "Other"

    text = description.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return "Other"
