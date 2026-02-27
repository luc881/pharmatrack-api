import unicodedata
import re


def slugify(text: str) -> str:
    """
    Converts a string to a normalized slug:
    - Lowercase
    - Removes accents and diacritics (á→a, é→e, ñ→n, ü→u, etc.)
    - Removes special characters
    - Replaces spaces with hyphens

    Examples:
        slugify("Amoxicilina")        → "amoxicilina"
        slugify("OFFENBACH MEXICANA") → "offenbach-mexicana"
        slugify("Antibióticos")       → "antibioticos"
        slugify("VANDIX 500MG")       → "vandix-500mg"
    """
    # 1. Lowercase
    text = text.lower().strip()
    # 2. Decompose unicode and remove diacritics (accents, tildes, etc.)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    # 3. Remove any character that is not alphanumeric or space
    text = re.sub(r"[^a-z0-9\s]", "", text)
    # 4. Replace whitespace with hyphens and collapse multiple spaces
    text = re.sub(r"\s+", "-", text)

    return text